# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen
import motor
import tornadoredis
from whoosh.fields import *
from whoosh.qparser import *


# c = tornadoredis.Client(host='162.243.37.124', port=6379)
# c.connect()

class IndexHandler(RequestHandler):
    #@asynchronous
    #@gen.coroutine
    def get(self):
        # keys = yield gen.Task(c.keys, pattern='grcount:San Fran*:lng')
        # locations = []
        # pipe = c.pipeline()
        # for key in keys:
        #     base = key[:key.rfind(':')]

        #     pipe.get(':'.join((base, 'lng')))
        #     pipe.get(':'.join((base, 'lat')))

        #     lng, lat = yield gen.Task(pipe.execute)

        #     locations.append((lng, lat))
        # print locations

        self.render('index.html', actors=None)

    def post(self):
        location = self.get_argument('location')
        return self.redirect('/search/%s' % location)
