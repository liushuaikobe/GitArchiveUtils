# -*- coding: utf-8 -*-
import requests
import os
import ujson
import time
import config


def load_cache(file_path=config.cache_file):
    """从文件中加载缓存"""
    try:
        f = open(config.cache_file, 'r')
        return ujson.load(f)
    except IOError:
        return {}


location_cache = load_cache() # 为避免每次都进行网络请求，将地名进行本地缓存
search_times = 0 # 请求网络的总次数
cache_hit = 0 # 本地缓存命中的次数

username_desperate = [] # 保存已经使用过的用户名
alarm = True # 当前用户名超限警报


def pickup_username():
    """找到一个可以用的Geoname用户名"""
    for u in config.username:
        if u not in username_desperate:
            username_desperate.append(u)
            return u

username = pickup_username()


def set_alarm():
    """设置警报，应该在某一批协程开始之前被调用"""
    alarm = True

def search_geo(location):
    """将location进行规范化处理，如果没找到对应的地名，则返回None"""
    global search_times, cache_hit, username, alarm
    search_times += 1
    if location.lower() in location_cache:
        cache_hit += 1
        # print 'hit'
        return location_cache[location.lower()]
    params = {'maxRows': config.result_num, 'username': username, 'q': location}

    # print 'requests %s' % location
    try:
        r = requests.get('http://api.geonames.org/searchJSON', params=params)
    except Exception, e:
        # 当某一个greenlet出现了异常，说明可能当前使用的username达到了访问次数的限制
        if alarm: # 警报还未解除，说明这一批的其他greenlet还没有人做出更换username的行动
            print 'Fire in the hole: %s max request times exceed!' % username
            username = pickup_username() # 更换新的用户名
            alarm = False # 告知其他greenlet警报解除
            print 'Clear.'
        # 休眠1分钟
        time.sleep(60)
        # 重新尝试
        params = {'maxRows': config.result_num, 'username': username, 'q': location}
        r = requests.get('http://api.geonames.org/searchJSON', params=params)
    # print 'get response %s.' % location

    # 只使用查询结果的第一条
    try:
        e = ujson.loads(r.text)['geonames'][0]
        regular_location = {
        # 'toponymName' 和 'name'的区别：http://goo.gl/Lbp14Q
        'name': e['name'] if 'name' in e else e['toponymName'].encode('utf-8'),
        'countryName': e['countryName'] if 'countryName' in e else e['countryCode'].encode('utf-8'),
        'lat': e['lat'],
        'lng': e['lng']
        }
    except (KeyError, IndexError):
        regular_location = None
    location_cache[location.lower()] = regular_location
    return regular_location


def cache_persistence(cache=location_cache, file_path=config.cache_file):
    """将缓存保存成文本文件"""
    with open(file_path, 'w') as f:
        ujson.dump(cache, f)
