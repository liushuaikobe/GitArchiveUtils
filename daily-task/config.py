# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:15:52

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 18:51:23
'''
import os


# debug
debug = True

# 能被称之为贡献的记录类型
contribution_type = ('IssuesEvent', 'PullRequestEvent', 'PushEvent')

# 数据库相关
db_addr = 'localhost'
db_port = 27017
db = 'sep'

# 协程相关
greenlet_num = 40

# 解析地名相关
result_num = 1 # 从服务器取回的结果条数
username = ('liushuaikobe','lskobe', 'lskobeqq')

# 缓存保存的位置
cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'location.txt')
redis_addr = 'localhost'
redis_port = 6379
redis_prefix = 'gitradar'

# 日志的位置
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')

# 数据保存的位置
data_base = '/home/liushuai/data'
# data_base = '/Users/liushuai/Downloads/data'

# 计算价值相关
credit = {
    'IssuesEvent': 0.1,
    'PullRequestEvent': 0.3,
    'PushEvent': 0.2
}

weight = {
    'star': 0.005,
    'fork': 0.005
}