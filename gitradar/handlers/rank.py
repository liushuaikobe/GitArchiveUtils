#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: liushuai
# @Date:   2013-12-22 21:44:19
# @Last Modified by:   liushuai
# @Last Modified time: 2013-12-22 21:57:26
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen
import ujson


class RankHandler(RequestHandler):
    """处理某一特定地区的排名"""
    @asynchronous
    @gen.coroutine
    def get(self, location):
        since_val = self.get_argument('since_val', default=None)
        since_name = self.get_argument('since_name', default=None)
        since_index = self.get_argument('since_index', default=0)
        num = int(self.get_argument('num', default=15))

        sort_rule = [('val', -1), ('login', 1)]

        if not (since_val and since_name and since_index):
            cursor = self.settings['db'].actor.find({'location.name': location}).sort(sort_rule).limit(num)
            actors = []
            while (yield cursor.fetch_next):
                actors.append(cursor.next_object())
            # print type(actors[0]['_id'])
            # 为actors中的每一个元素添加下标
            for i, actor in enumerate(actors):
                actor['index'] = i + 1
            self.render('rank.html', actors=actors, location=location)
        else:
            since_val = float(since_val)
            EPSINON = 0.000001
            query_string = {
                'location.name': location,
                'val': {
                    '$gt': since_val - EPSINON,
                    '$lt': since_val + EPSINON
                },
                'login': {
                    '$gt': since_name
                }
            }
            # 由于要以JSON的形式返回，查询时不返回actor的_id(无法被JSON序列化)
            cursor = self.settings['db'].actor.find(query_string, {'_id': 0}).sort(sort_rule).limit(num)
            actors = []
            while(yield cursor.fetch_next):
                actors.append(cursor.next_object())
            if len(actors) < num:
                query_string = {
                    'location.name': location,
                    'val': {
                        '$lt': since_val
                    },
                }
                cursor = self.settings['db'].actor.find(query_string, {'_id': 0}).sort(sort_rule).limit(num - len(actors))
                while(yield cursor.fetch_next):
                    actors.append(cursor.next_object())
            # 添加下标
            for i, actor in enumerate(actors):
                actor['index'] = int(since_index) + i + 1
            self.write(ujson.dumps(actors))
        
