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
        self.greenlet_num = config.greenlet_num 
        self.webservice_cache = {} 
        self.new_actors = {} # 今日新增的用户和他们的规范化信息

        self.username = self.pickup_username()
        self.username_desperate = []

    def set_record(self, r):
        self.records = r

    def archive_by_location(self):
        for i, record in enumerate(self.records):
            location = record['actor_attributes']['location']
            if location in self.webservice_cache:
                self.webservice_cache[location].append(i)
            else:
                self.webservice_cache[location] = [i]

    def process_trick_actor(self, trick_actor_indexes):
        for i in trick_actor_indexes:
            del self.records[i]

    def process_good_actor(self, good_actor_indexes, regular_location):
        for i in good_actor_indexes:
            r = self.records[i]
            actor = r['actor']
            attrs = r['actor_attributes']
            attrs['location'] = regular_location
            self.new_actors[actor] = attrs # 因为用字典保存，因此直接做更新即可，后面重复的自动覆盖
            del self.records[i]['actor_attributes']

    def process(self):
        # 对所有记录尝试从缓存中进行规范化
        for location in self.webservice_cache:
            regular_location = self.cache.get_location(location)
            if regular_location == -1:
                self.process_trick_actor(self.webservice_cache[location])
                del self.webservice_cache[location]
            else if regular_location is not None:
                self.process_good_actor(self.webservice_cache[location], regular_location)
                del self.webservice_cache[location]

        # 对剩下的记录，不得不尝试调用Web Service来进行规范化
        locations = self.webservice_cache.keys()
        webservice_result = {}
        i = 0
        while i < len(locations):
            jobs = [gevent.spawn(self.search, l) for l in locations[i:i+self.greenlet_num]]
            gevent.joinall(jobs)
            for r in jobs:
                webservice_result[r.value['origin']] = r.value
            i += self.greenlet_num

        # 将来之不易的数据缓存
        for r in webservice_result:
            self.cache.put_location(r, webservice_result[i], False)
        self.cache.execute()

        for location in self.webservice_cache:
            regular_location = webservice_result[location]
            if regular_location == None:
                self.process_trick_actor(self.webservice_cache[location])
            else:
                self.process_good_actor(self.webservice_cache[location], regular_location)

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
                'lng': e['lng'],
                'origin': location
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

    def normalize(self):
        self.archive_by_location()
        self.process()







