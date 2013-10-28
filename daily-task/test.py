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

for i in xrange(100):
    jobs = [gevent.spawn(utils.search_geo, i) for i in ['Harbin', 'Shanghai', 'haha', 'fuck', 'hangzhou', 'Los Angeles', 'DC', 'AB', 'Beijing', 'Nanjing']]
    gevent.joinall(jobs)