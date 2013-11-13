# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:14:12

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 15:03:21
'''
import config
import decorator


class Grouper(object):
    """将每天的记录按actor是否已经在DB中分成两组"""
    def __init__(self, client):
        self.client = client # 数据库客户端
        self.bulk_num = 1000
        self.cache = {} # 当需要查询的actor达到bulk_num时，将发送一次查询请求
        self.records = [] # 待处理的记录
        self.group_1 = [] # Actor已经存在的记录
        self.group_2 = [] # Actor之前不存在的记录，可能是该用户最近添加了location信息等等

    def set_record(self, r):
        self.records = r

    @decorator.log('Data grouping...', 'Grouping finished.')
    def group(self):
        """分组"""
        for record in self.records:
            actor = record['actor_attributes']['login']
            if actor in self.cache:
                self.cache[actor].append(record)
            else:
                self.cache[actor] = [record]
            if len(self.cache) == self.bulk_num:
                result = self.query()
                self.process(result)

    def query(self):
        """发送查询请求"""
        actors = self.cache.keys()
        result = self.client[config.db].actor.find({"login": {"$in": actors}}, {"login": 1})
        return [r['login'] for r in result] # 在DB中已存在的记录

    def process(self, exist_actors):
        """根据查询结果将record添加到不同的组里，并清空cache"""
        for c in self.cache:
            if c in exist_actors:
                self.group_1.extend(self.cache[c])
            else:
                self.group_2.extend(self.cache[c])
        self.cache.clear()

    def get_group_1(self):
        return self.group_1

    def get_group_2(self):
        return self.group_2