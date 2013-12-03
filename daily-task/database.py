# -*- coding: utf-8 -*-
'''
Created on 2013-11-14 16:11:44

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-14 16:11:44
'''
import decorator

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

