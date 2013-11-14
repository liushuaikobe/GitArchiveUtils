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
from .cache import LocationCache




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
        self.greenlet_num = config.greenlet_num # 当要调用Web Service的个数达到了该值时，并发发起一批调用
        self.webservice_cache = {} # （接上一行）未达到时暂时缓存在此
        self.new_actors = {} # 今日新增的用户和他们的规范化信息
        self.trick_actors = set([]) # location不准确的用户，例如：“/dev/null”,“The earth”

        self.username = self.pickup_username()
        self.username_desperate = []

    def set_record(self, r):
        self.records = r

    def normalize(self):
        for i, record in enumerate(self.records):
            actor = record['actor']

            # 之前已经处理过该用户的行为记录，并已经规范化过

            if actor in self.new_actors:
                # 只需删掉这条记录的actor_attributes
                del record['actor_attributes']
                continue
            if actor in self.trick_actors:
                continue

            # 第一次遇见该用户的行为记录

            attrs = record['actor_attributes']
            location = attrs['location']

            cache_result = self.cache.get_location(location)
            # 根据缓存结果不同做出不同处理
            if cache_result == -1:
                # 把该用户加入到trick_actor，在将来这条记录要删除
                self.trick_actors.add(actor)
            else if cache_result is not None:
                self.process_new_actor(attrs, cache_result)
                del record['actor_attributes']
            else:
                if location in self.webservice_cache:
                    self.webservice_cache[location].append(i)
                else:
                    self.webservice_cache[location] = [i]
                    if len(self.webservice_cache) == self.greenlet_num:
                        try:
                            jobs = [gevent.spawn(self.search, l) for l in self.webservice_cache]
                            gevent.joinall(jobs)
                            for i, l in enumerate(self.webservice_cache):
                                for j in self.webservice_cache[l]:
                                    search_result = jobs[i].value
                                    self.cache.put_location(l, search_result)
                                    if search_result:
                                        self.process_new_actor(self.records[j]['actor_attributes'], search_result)
                                    else:
                                        self.trick_actors.add(self.records[j]['actor'])
                        except Exception, e:
                            pass

        def process_new_actor(self, actor_attributes, regular_location):
            regular_location['origin'] = actor_attributes['location']
            actor_attributes['location'] = regular_location
            # 把该用户添加到new_actors
            self.new_actors[actor_attributes['login']] = actor_attributes


        def search(self, location):
            params = {'maxRows': config.result_num, 'username': self.username, 'q': location}
            r = requests.get('http://api.geonames.org/searchJSON', params=params)
            try:
                e = ujson.loads(r.text)['geonames'][0]
                regular_location = {
                    # 'toponymName' 和 'name'的区别：http://goo.gl/Lbp14Q
                    'name': e['name'] if 'name' in e else e['toponymName'].encode('utf-8'),
                    'countryName': e['countryName'] if 'countryName' in e else e['countryCode'].encode('utf-8'),
                    'lat': e['lat'],
                    'lng': e['lng']
                }
            except (KeyError, IndexError):
                regular_location = None
            return regular_location


        def pickup_username():
            """找到一个可以用的Geoname用户名"""
            for u in config.username:
                if u not in self.username_desperate:
                    self.username_desperate.append(u)
                    return u











