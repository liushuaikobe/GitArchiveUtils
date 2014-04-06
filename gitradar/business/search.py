#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: liushuai
# @Date:   2013-12-23 09:44:14
# @Last Modified by:   liushuai
# @Last Modified time: 2013-12-23 09:46:05
from tornado.options import options
from whoosh.index import open_dir
from whoosh.fields import *
from whoosh.qparser import *


class GRSearcher(object):
    """封装了Whoosh搜索地名的一些方法"""
    def __init__(self, index_dir):
        super(GRSearcher, self).__init__()
        self.ix = open_dir(index_dir)
        self.search_on = 'location'
        self.parser = QueryParser(self.search_on, self.ix.schema)

    def search(self, search_txt):
        with self.ix.searcher() as searcher:
            q = self.parser.parse(search_txt)
            # 尝试correct检索词
            corrected_search_txt = self.correct(searcher, search_txt)
            results = searcher.search(q, limit=10)
            locations = [result['location'] for result in results]
            rlocations = [result['rlocation'] for result in results]
            return corrected_search_txt, locations, rlocations

    def correct(self, searcher, search_txt):
        corrector = searcher.corrector(self.search_on)
        return corrector.suggest(search_txt)
