# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import gevent
import requests
import utils


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

def main():
    for i in range(100):
        jobs = [gevent.spawn(utils.search_geo, i) for i in ['Harbin', 'Shanghai', 'haha', 'fuck', 'hangzhou', 'Los Angeles', 'DC', 'AB', 'Beijing', 'Nanjing']]
        gevent.joinall(jobs)


if __name__ == '__main__':
    # main()
    for j in range(100): 
        jobs = [gevent.spawn(test3, i) for i in ['Harbin', 'Shanghai', 'haha', 'fuck', 'hangzhou', 'Los Angeles', 'DC', 'AB', 'Beijing', 'Nanjing'] * 10]
        gevent.joinall(jobs)
        print '%s passed.' % j 