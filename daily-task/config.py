# -*- coding: utf-8 -*-
import os


# debug
debug = False

# 能被称之为贡献的记录类型
contribution_type = ('IssuesEvent', 'PullRequestEvent', 'PushEvent')

# 数据库相关
db_addr = '172.16.0.1'
db_port = 27017
db = 'op_test'

# 协程相关
greenlet_num = 40

# 解析地名相关
result_num = 1 # 从服务器取回的结果条数
username = 'liushuaikobe'

# 缓存保存的位置
redis_addr = '172.16.0.1'
redis_port = 6379
redis_prefix = 'gitradar'

# 日志的位置
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')

# 数据保存的位置
data_base = '/home/footoo/githubradar/data'
# data_base = '/Users/liushuai/Downloads/data'

# 邮件相关
mail_config = {
    'from': 'gitradar@163.com',
    'to': 'liushuaikobe@gmail.com',
    'server': 'smtp.163.com',
    'username': 'gitradar',
    'pwd': 'footoo!@#$'
}

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