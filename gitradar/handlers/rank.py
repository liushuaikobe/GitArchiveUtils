#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: liushuai
# @Date:   2013-12-22 21:44:19
# @Last Modified by:   liushuai
# @Last Modified time: 2013-12-22 21:57:26
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen


class RankHandler(RequestHandler):
    """处理某一特定地区的排名"""
    @asynchronous
    @gen.coroutine
    def get(self, location):
        cursor = self.settings['db'].actor.find({'location.name': location}).sort([('val', -1)])
        actors = []
        while (yield cursor.fetch_next):
            actors.append(cursor.next_object())
        self.render('rank.html', actors=actors)
        