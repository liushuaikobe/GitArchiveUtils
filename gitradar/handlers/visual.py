# -*- coding: utf-8 -*-
from tornado.web import RequestHandler


class VisualHandler(RequestHandler):
    def get(self):
        self.render('visual.html')
