# -*- coding: utf-8 -*-
import redis

import decorator
import config



class MongoHelper(object):
    def __init__(self, db):
        self.db = db
        self.bulk_num = 1500

    @decorator._log('Insert new actor...', 'Finished.')
    def insert_new_actors(self, actors):
        """将今日新增的actor插入数据库，应该进行bulk insert以提高效率"""
        i = 0
        while i < len(actors):
            self.db.actor.insert(actors[i:i+self.bulk_num])
            i += self.bulk_num

    @decorator._log('Insert records...', 'Finished.')
    def insert_new_reocrds(self, records):
        """将今日的所有记录插入数据库，应该进行bulk insert以提高效率"""
        i = 0
        while i < len(records):
            self.db.event.insert(records[i:i+self.bulk_num])
            i += self.bulk_num

    @decorator._log('Update the val of each user...', 'Finished.')
    def update_val(self, actor_val):
        """将今日所有用户新增加的分数更新到数据库中"""
        for actor in actor_val:
            self.db.actor.update({"login": actor}, {"$inc": {"val": actor_val[actor]}})


redis_pool = None


def get_redis_connection():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(host=config.redis_addr, port=config.redis_port)
    return redis.Redis(connection_pool=redis_pool)


def get_redis_pipeline():
    r = get_redis_connection()
    return r.pipeline(transaction=False)
