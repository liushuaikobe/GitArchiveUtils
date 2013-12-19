# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import time

import gevent
import requests
import ujson
from requests.exceptions import RequestException, ConnectionError, Timeout

import config
import log
import decorator
import database
import util
from util import WhooshUtil
from cache import LocationCache


class Normalizer(object):
    """对一坨记录的位置信息进行规范化处理
    注意：没有规范化结果的record直接予以删除
    """
    def __init__(self, db):
        self.db = db
        self.records = [] # 待处理的一坨记录
        self.new_actors = {} # 今日新增的用户和他们的规范化信息

        self.greenlet_num = config.greenlet_num # 并发数量
        self.cache = LocationCache() # 地名缓存对象
        self.webservice_cache = {}  # 对记录按着地名归档后的结果，{'Hangzhou': [1, 2, 3], 'BeiJing': [5, 7, 8]}

        self.username = config.username # 当前Geonames的用户名

        self.trick_record_indices = [] # 地名信息规范化没有结果的记录的下标

        self.webservice_result = {} #  规范化结果

        self.failed_locations = set([]) # 调用Web Service失败的location

        self.whoosh_util = WhooshUtil()

    def set_records(self, r):
        self.records = r

    def archive_by_location(self):
        """将待处理的记录按着location信息归档"""
        for i, record in enumerate(self.records):
            location = record['actor_attributes']['location'].encode('utf-8')
            if location in self.webservice_cache:
                self.webservice_cache[location].append(i)
            else:
                self.webservice_cache[location] = [i]

    def process_trick_actor(self, trick_record_indices):
        self.trick_record_indices.extend(trick_record_indices)

    def process_good_actor(self, good_actor_indices, regular_location):
        for i in good_actor_indices:
            r = self.records[i]
            actor = r['actor']
            attrs = r['actor_attributes']
            attrs['location'] = regular_location
            self.new_actors[actor] = attrs # 因为用字典保存，因此直接做更新即可，后面重复的自动覆盖
            del self.records[i]['actor_attributes']

    def clean_trick_records(self):
        # 这样删除是错误的，在数组中，删除一个元素，它后面元素的索引也随之变化。见：http://goo.gl/PHwtcE
        # for i in self.trick_record_indices:
        #     del self.records[i]
        self.trick_record_indices.sort(reverse=True)
        for i in self.trick_record_indices:
            del self.records[i]

    def process(self):
        # 首先，对所有记录尝试从缓存中进行规范化
        log.log('Try to Normalize from cache...%s total in webservice_cache.' % len(self.webservice_cache))

        cached_location = set([]) # 在缓存中找到的location

        for location in self.webservice_cache:
            regular_location = self.cache.get_location(location)

            if regular_location == -1:
                self.process_trick_actor(self.webservice_cache[location])
                cached_location.add(location)
            elif regular_location is not None:
                self.process_good_actor(self.webservice_cache[location], regular_location)
                cached_location.add(location)

        # 已经从本地缓存中找到的location，就不必去调用Web Service了
        for l in cached_location:
            del self.webservice_cache[l]

        log.log('Finished. %s remain.' % len(self.webservice_cache))


        # 对剩下的记录，不得不尝试调用Web Service来进行规范化
        log.log('Have to Normalize via Web Service...')

        locations = self.webservice_cache.keys()

        i = 0
        while i < len(locations):
            self.invoke_webservice_task(locations[i:i + self.greenlet_num])
            log.log('%.2f%% finished.' % (float(i) / float(len(locations)) * 100))
            i += self.greenlet_num


        # 调用Web Service出现异常的location，再次尝试规范化
        log.log('Retry Failed Location...%s total.' % len(self.failed_locations))

        locations = list(self.failed_locations)

        i = 0
        while i < len(locations):
            self.invoke_webservice_task(locations[i:i + self.greenlet_num], final=True)
            log.log('%.2f%% finished.' % (float(i) / float(len(locations)) * 100))
            i += self.greenlet_num

        log.log('Retry Finished.')

        # 建立whoosh搜索索引
        self.whoosh_util.build_whoosh_index()
        for r in self.webservice_result:
            # 将来之不易的数据缓存
            self.cache.put_location(r, self.webservice_result[r], execute_right_now=False)
            # 添加到whoosh搜索
            self.whoosh_util.add_search_doc(r, self.webservice_result[r], execute_right_now=False)
        self.cache.execute()
        self.whoosh_util.commit()


        # 根据Web Service的结果继续处理记录
        for location in self.webservice_cache:
            try:
                regular_location = self.webservice_result[location]
                try:
                    if regular_location == None:
                        self.process_trick_actor(self.webservice_cache[location])
                    else:
                        self.process_good_actor(self.webservice_cache[location], regular_location)
                except KeyError:
                    log.log('Hope this will never happen.')
                    raise e
            except KeyError: # 出现了KeyError说明，该location由于某种异常未能正确解析出结果
                assert(location in self.failed_locations) # 那么可以断言，该location一定在self.failed_locations中
                # 由于未能解析出结果的location对应的记录已经被插入到异常数据库
                log.log('Get KeyError!')
                self.process_trick_actor(self.webservice_cache[location])

    def invoke_webservice_task(self, locations, final=False):
        """利用Python的协程技术将locations中的地名通过Web Sservice得到其规范化的信息，
        将结果存入实例变量self.webservice_result中
        """
        greenlets = [gevent.spawn(self.search, l) for l in locations]
        gevent.joinall(greenlets)

        alarm = False

        for greenlet in greenlets:
            arg = greenlet.value[0] # arg为传进该greenlet的参数(待规范化的location)
            result = greenlet.value[1]

            if result != -1: # 该greenlet正常得到了结果
                self.webservice_result[arg] = result
            else: # 该greenlet未正常执行
                alarm = True
                if final: # 如果final参数被置为True，则出异常后直接将异常location在self.webservice_cache对应的记录插入到数据库中
                    exception_records = [self.records[i] for i in self.webservice_cache[arg]]
                    self.db.exception.insert(exception_records)
                    util.sendmail('Exception', '%s records did not be handled right.' % len(exception_records))
                else:
                    log.log('Greenlet with %s end up with an error, %s records in webservice_cache.' % 
                        (arg, len(self.webservice_cache[arg])))
                    self.failed_locations.add(arg)
        if alarm:
            log.log('Go sleeping...')
            time.sleep(60 * 3)
            log.log('Wake up!')

    def search(self, location):
        """greenlet，无论执行结果如何，参数location都做为返回结果的第一个参数返回"""
        params = {'maxRows': config.result_num, 'username': self.username, 'q': location}
        try:
            r = requests.get('http://api.geonames.org/searchJSON', params=params, timeout=10) # timeout = 10s
        except ConnectionError, e: # Connection reset by peer
            log.log('ConnectionError=。=: %s' % str(e), log.ERROR)
            return location, -1
        except Timeout, e: # 网速慢等原因导致的超时
            log.log('Requests Timeout=。=: %s' % str(e), log.ERROR)
            return location, -1
        except RequestException, e:
            log.log('RequestException=。=: %s' % str(e), log.ERROR)
            return location, -1 # 第二个返回值是-1表示该greenlet异常
        try:
            e = ujson.loads(r.text)['geonames'][0]
            regular_location = {
                # 'toponymName' 和 'name'的区别：http://goo.gl/Lbp14Q
                'name': e['name'].encode('utf-8') if 'name' in e else e['toponymName'].encode('utf-8'),
                'countryName': e['countryName'].encode('utf-8') if 'countryName' in e else e['countryCode'].encode('utf-8'),
                'lat': e['lat'].encode('utf-8'),
                'lng': e['lng'].encode('utf-8'),
                'origin': location
            }
        except (KeyError, IndexError):
            regular_location = None
        return location, regular_location

    @decorator._log('Normalizing...', 'Normalizing finished.')
    def normalize(self):
        self.archive_by_location()
        self.process()
        self.clean_trick_records()

    def get_new_actors(self):
        return self.new_actors

    def get_record_actor_exist(self):
        return self.records
