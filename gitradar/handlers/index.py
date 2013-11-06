# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen
import motor


class IndexHandler(RequestHandler):
    def get(self):
        self.render('index.html', actors=None)

    @asynchronous
    @gen.coroutine
    def post(self):
        q = self.get_argument('location')
        cursor = self.settings['db'].actor.find({'location.name': q}).sort([('val', -1)])
        actors = []
        while (yield cursor.fetch_next):
            actors.append(cursor.next_object())
        self.render('index.html', actors=actors)