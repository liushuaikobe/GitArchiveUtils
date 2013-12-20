# -*- coding: utf-8 -*-
import datetime

import redis

import log
import config
from count import Counter
from database import get_redis_pipeline


class Cache(object):
    """缓存的基类"""
    def __init__(self):
        self.pipe = get_redis_pipeline() # 获取Redis的pipeline

    def get(self, key):
        return self.pipe.get(self.format_key(key))

    def set(self, key, val):
        return self.pipe.set(self.format_key(key), val)

    def execute(self):
        return self.pipe.execute()

    def format_key(self, key):
        return '{0}:{1}'.format(config.redis_prefix, key)


class LocationCache(Cache):
    """地名的缓存，以减少调用WebService的次数"""
    def __init__(self):
        super(LocationCache, self).__init__()
        self.counter = Counter(prefix=config.redis_info_prefix)
        self.search_count = 0 # 用于记录查询的总次数
        self.hit_count = 0 # 用于记录缓存的命中次数
        
    def put_location(self, location, regular_location, execute_right_now=True):
        l_location = location.lower()
        if regular_location is None:
            self.set(':'.join((l_location, 'origin')), -1)
        else:
            for e in regular_location:
                self.set(':'.join((l_location, e)), regular_location[e])
        if execute_right_now:
            self.execute()

    def get_location(self, location):
        self.search_count += 1
        l_location = location.lower()
        self.get(':'.join((l_location, 'origin')))
        self.get(':'.join((l_location, 'name')))
        self.get(':'.join((l_location, 'countryName')))
        self.get(':'.join((l_location, 'lat')))
        self.get(':'.join((l_location, 'lng')))
        result = self.execute()
        if result[0] is None:
            # 缓存未命中
            # log.log('missing => %s' % location, log.DEBUG)
            return None
        elif result[0] == '-1':
            # 缓存命中，但之前没有规范化的结果，是一个trick_actor
            # log.log('hit trick => %s' % location, log.DEBUG)
            self.hit_count += 1
            return -1
        else:
            # 缓存命中，是一个非常给力的用户：）
            # log.log('hit normal => %s' % location, log.DEBUG)
            self.hit_count += 1
            return {
                'name': result[1],
                'countryName': result[2],
                'lat': result[3],
                'lng': result[4],
                'origin': location
            }

    def set_hit_result(self):
        """将缓存的命中情况更新到数据库
        因为是每天的任务，故用当天的日期作为中缀，并采取累加的方式来计数
        """
        infix = datetime.datetime.now().strftime("%Y%m%d")
        self.counter.inc_n(infix, 'search', self.search_count, execute_right_now=False)
        self.counter.inc_n(infix, 'hit', self.hit_count, execute_right_now=False)
        self.counter.execute()
