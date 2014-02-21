# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import gevent
import requests
from whoosh.index import open_dir
from whoosh.fields import *
from whoosh.qparser import *

import decorator
import util
from util import WhooshUtil


def foo(o):
    del o['a']

def test1():
    a = {'a':1, 'b':2}
    print a
    foo(a)
    print a

def test2():
    a = range(107)
    i = 0
    while i < len(a):
        print a[i:i+10]
        i += 10

def task(i):
    print "requests %s" % i
    requests.get("http://www.baidu.com")
    print "finish %s" % i


def test3(q):
    params = {'q':q, 'maxRows':10, 'username':'liushuaikobe'}
    r = requests.get('http://api.geonames.org/searchJSON', params=params)
    if r.status_code != 200:
        print r.status_code

t41 = []
def test4(r):
    t41.extend(r)
    print t41


def test5():
    a = range(200)
    i = 0
    while len(a) > 37:
        test4(a[:37])
        del a[:37]
    if a:
        test4(a)
        del a
    print a


def test6():
    for j in range(100): 
        jobs = [gevent.spawn(test3, i) for i in ['Harbin', 'Shanghai', 'haha', 'fuck', 'hangzhou', 'Los Angeles', 'DC', 'AB', 'Beijing', 'Nanjing'] * 10]
        gevent.joinall(jobs)
        print '%s passed.' % j 

@decorator._log('fuck', 'haha')
def test7():
    print 'in test7'

def test8():
    return 2 / 0

def test9():
    try:
        test8()
    except Exception, e:
        print 'fuckkk...'

def test10():
    10 / 0

def test12_onError():
    pass

def test11():
    try:
        jobs = [gevent.spawn_link_exception(test10) for _ in range(10)]
        gevent.joinall(jobs)
    except Exception, e:
        print 'liushuaikobe~~!!'

def test13():
    try:
        1 / 0
    except Exception, e:
        return 'lskobe'

def test14():
    util.sendmail('fuck', 'Test')

def test15():
    print util.detect('/Users/liushuai/Downloads/data/2013/11/3', 2013, 11, 3)

def test16():
    requests.get('https://github.com', timeout=0.001)

def test17():
    greenlet = gevent.spawn(test10)
    greenlet.join()
    print type(greenlet.exception)

def test18():
    for j in range(24):
        wu = WhooshUtil(ix_path='/Users/liushuai/temp/index')
        wu.build_whoosh_index()

        for i in range(j * 10, j * 10 + 10):
            print i
            wu.add_search_doc(location=str(i), rlocation='fuck', execute_right_now=False)

        wu.commit()

def test19():
    ix = open_dir('/Users/liushuai/temp/index')
    print 'doc count', ix.doc_count()

    with ix.searcher() as searcher:
        parser = QueryParser('location', ix.schema)
        while True:
            search_txt = raw_input()
            q = parser.parse(search_txt)
            results = searcher.search(q, limit=None)
            for r in results:
                print r.fields()

def test20():
    util.grcount2csv()

if __name__ == '__main__':
    test20()
