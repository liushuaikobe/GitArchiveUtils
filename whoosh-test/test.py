#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: liushuai
# @Date:   2013-12-18 15:37:45
# @Last Modified by:   liushuai
# @Last Modified time: 2013-12-19 19:03:24

import os

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import *


schema = Schema(location=TEXT(stored=True), link=TEXT)

if not os.path.exists('ix'):
    os.mkdir('ix')
ix = create_in('ix', schema)

writer = ix.writer()

locations = open('location.txt', 'r')
for line in locations:
    # print line
    writer.add_document(location=unicode(line.strip(), 'utf-8'), link=u'fuck')
writer.commit()

with ix.searcher() as searcher:
    parser = QueryParser('location', ix.schema)
    while True:
        search_txt = raw_input()
        q = parser.parse(search_txt)
        results = searcher.search(q)
        for r in results:
            print r.fields()

