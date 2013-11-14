# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 17:23:13

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 20:37:25
'''
import redis
import config


class Cache(object):
    """缓存的基类"""
    redis_pool = None

    def __init__(self):
        self.pipe = self.get_pipeline() # 获取Redis的pipeline

    def get_connection(self):
        if Cache.redis_pool is None:
            Cache.redis_pool = redis.ConnectionPool(port=config.redis_port)
        return redis.Redis(connection_pool=Cache.redis_pool)

    def get_pipeline(self):
        r = self.get_connection()
        return r.pipeline(transaction=False)

    def get(self, key):
        return self.pipe.get(self.format_key(key))

    def set(self, key, val):
        return self.pipe.set(self.format_key(key), val)

    def execute(self):
        return self.pipe.execute()

    def format_key(key):
        return '{0}:{1}'.format(config.redis_prefix, key)




class LocationCache(Cache):
    """地名的缓存，以减少调用WebService的次数"""
    def __init__(self):
        super(LocationCache, self).__init__()
        self.search_count = 0 # 用于记录查询的总次数
        self.hit_count = 0 # 用于记录缓存的命中次数
        
    def put_location(self, location, regular_location, execute_right_now=True):
        if regular_location is None:
            self.set(location, -1)
        else:
            for e in regular_location:
                self.set(':'.join((location, e)), regular_location[e])
        if execute_right_now:
            self.execute()

    def get_location(self, location):
        self.search_count += 1
        self.get(location)
        self.get(':'.join((location, 'name')))
        self.get(':'.join((location, 'countryName')))
        self.get(':'.join((location, 'lat')))
        self.get(':'.join((location, 'lng')))
        result = self.execute()
        if result[0] is None:
            # 缓存未命中
            return None
        else if int(result[0]) == -1:
            # 缓存命中，但之前没有规范化的结果，是一个trick_actor
            self.hit_count += 1
            return -1
        else:
            # 缓存命中，是一个非常给力的用户：）
            self.hit_count += 1
            return {
                'name': result[1],
                'countryName': result[2],
                'lat': result[3],
                'lng': result[4],
                'origin': location
            }

        def set_hit_result(self):
            """将缓存的命中情况更新到数据库"""
            pass







