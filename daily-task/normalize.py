# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 15:14:42

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 22:02:10
'''
from gevent import monkey
monkey.patch_all()
import gevent
import requests
import ujson
import config
import log
import decorator
from functools import partial
from cache import LocationCache
from requests.exceptions import RequestException, ConnectionError


class Normalizer(object):
    """
    对一坨记录进行规范化处理
    处理流程：
    1.  把每条记录的actor_attributes中的location的值替换为规范化的结果
        规范化的结果如：
        {
            "countryName": "China",
            "lat": "31.30408",
            "lng": "120.59538",
            "name": "Suzhou",
            "origin": "Suzhou, China"
        }
        其中"origin"的值是用户自己填写的位置信息

    2.  之后把记录的actor_attributes加入保存今日新增的用户的字典(self.new_actors)
        如：
        {
            "liushuaikobe": {
                "countryName": "China",
                "lat": "31.30408",
                "lng": "120.59538",
                "name": "Suzhou",
                "origin": "Suzhou, China"
            }
        }

    3.  删除记录的actor_attributes属性

    注意：没有规范化结果的record直接予以删除
    """
    def __init__(self):
        self.cache = LocationCache()
        self.records = [] # 待处理的一坨记录
        self.greenlet_num = config.greenlet_num 
        self.webservice_cache = {} 
        self.new_actors = {} # 今日新增的用户和他们的规范化信息

        self.username_desperate = []
        self.username = self.pickup_username()

        self.trick_actor_indices = []

        self.webservice_result = {} # 每次发起的协程任务的返回结果

    def set_records(self, r):
        self.records = r

    def archive_by_location(self):
        for i, record in enumerate(self.records):
            location = record['actor_attributes']['location'].encode('utf-8')
            if location in self.webservice_cache:
                self.webservice_cache[location].append(i)
            else:
                self.webservice_cache[location] = [i]

    def process_trick_actor(self, trick_actor_indices):
        self.trick_actor_indices.extend(trick_actor_indices)

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
        # for i in self.trick_actor_indices:
        #     del self.records[i]
        self.trick_actor_indices.sort(reverse=True)
        for i in self.trick_actor_indices:
            del self.records[i]

    def process(self):
        # 首先，对所有记录尝试从缓存中进行规范化
        log.log('Try to Normalize from cache...%s total in webservice_cache.' % len(self.webservice_cache))
        l_found_in_cache = set([]) # 在缓存中找到的location
        for location in self.webservice_cache:
            regular_location = self.cache.get_location(location)
            if regular_location == -1:
                self.process_trick_actor(self.webservice_cache[location])
                l_found_in_cache.add(location)
            elif regular_location is not None:
                self.process_good_actor(self.webservice_cache[location], regular_location)
                l_found_in_cache.add(location)
        for l in l_found_in_cache:
            del self.webservice_cache[l]
        log.log('Finished. %s remain.' % len(self.webservice_cache))

        # 对剩下的记录，不得不尝试调用Web Service来进行规范化
        log.log('Have to Normalize via Web Service...')
        locations = self.webservice_cache.keys()
        i = 0
        while i < len(locations):
            self.invoke_webservice_task(locations[i:i+self.greenlet_num])
            log.log('%.2f%% finished.' % (float(i) / float(len(locations)) * 100))
            i += self.greenlet_num

        # 将来之不易的数据缓存
        for r in self.webservice_result:
            self.cache.put_location(r, self.webservice_result[r], False)
        self.cache.execute()

        for location in self.webservice_cache:
            regular_location = self.webservice_result[location]
            if regular_location == None:
                self.process_trick_actor(self.webservice_cache[location])
            else:
                self.process_good_actor(self.webservice_cache[location], regular_location)

    def invoke_webservice_task(self, locations):
        """利用Python的协程技术将locations中的地名通过webservice得到其规范化的信息，
        将结果存入实例变量self.webservice_result中
        """
        jobs = [gevent.spawn(self.search, l) for l in locations]
        x = [j.link_exception(partial(self.on_webservice_error, 
            partial(self.invoke_webservice_task, locations))) for j in jobs]
        gevent.joinall(jobs)
        for j in jobs:
            if j is None:
                continue
            self.webservice_result[j.value[0]] = j.value[1]

    def on_webservice_error(self, func, greenlet):
        """执行调用WebService任务的某一个协程出现了错误时，被调用"""
        log.log(greenlet.exception, log.ERROR)
        if 'reset' in greenlet.exception:
            log.log('Fire in the hole: %s max request times exceed!' % self.username, log.WARNING)
            self.username = self.pickup_username()
            log.log('Username change to %s.' % self.username, log.WARNING)
        func()

    def search(self, location):
        log.log('Requests => %s' % location)
        params = {'maxRows': config.result_num, 'username': self.username, 'q': location}
        r = requests.get('http://api.geonames.org/searchJSON', params=params)
        log.log('Get Response => %s' % location)
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


    def pickup_username(self):
        """找到一个可以用的Geoname用户名"""
        for u in config.username:
            if u not in self.username_desperate:
                self.username_desperate.append(u)
                return u

    @decorator._log('Normalizing...', 'Normalizing finished.')
    def normalize(self):
        self.archive_by_location()
        self.process()
        self.clean_trick_records()

    def get_new_actors(self):
        return self.new_actors

    def get_record_actor_exist(self):
        return self.records
