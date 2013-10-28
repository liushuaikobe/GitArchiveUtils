# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import requests
import os
import ujson
import config


location_cache = {} # 为避免每次都进行网络请求，将地名进行本地缓存
search_times = 0
cache_hit = 0

def search_geo(location):
    """将location进行规范化处理，如果没找到对应的地名，则返回None"""
    global search_times, cache_hit
    search_times += 1
    if location.lower() in location_cache:
        cache_hit += 1
        print 'hit'
        return location_cache[location.lower()]
    params = {'maxRows': config.result_num, 'username': config.username, 'q': location}
    print 'requests'
    r = requests.get('http://api.geonames.org/searchJSON', params=params)
    print 'get response.'
    # 只使用查询结果的第一条
    try:
        e = ujson.loads(r.text)['geonames'][0]
        regular_location = {
        # 'toponymName' 和 'name'的区别：http://goo.gl/Lbp14Q
        'name': e['name'].encode('utf-8') if 'name' in e else e['toponymName'].encode('utf-8'),
        'countryName': e['countryName'].encode('utf-8') if 'countryName' in e else e['countryCode'].encode('utf-8'),
        'lat': e['lat'].encode('utf-8'),
        'lng': e['lng'].encode('utf-8')
        }
    except (KeyError, IndexError):
        regular_location = None
    location_cache[location.lower()] = regular_location
    return regular_location


def cache_persistence(cache, name='cache.txt'):
    """将cache保存成文本文件"""
    cahce_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', name)
    with open(cahce_file, 'w') as f:
        f.write(str(cache))
