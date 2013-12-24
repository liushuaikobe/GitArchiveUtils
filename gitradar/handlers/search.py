# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen


class SearchHandler(RequestHandler):
    def get(self, location):
        searcher = self.settings['searcher']
        clocations, locations, rlocations = searcher.search(location)
        self.render('search_result.html', clocations=clocations, locations=locations, rlocations=rlocations)



