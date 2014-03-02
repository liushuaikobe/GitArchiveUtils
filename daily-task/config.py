# -*- coding: utf-8 -*-
import os
import datetime


# debug
debug = False

# 能被称之为贡献的记录类型
contribution_type = ('IssuesEvent', 'PullRequestEvent', 'PushEvent')

# 数据库相关
db_addr = '127.0.0.1'
db_port = 27017
db = 'op_test_debug'

# 协程相关
greenlet_num = 40

# 解析地名相关
result_num = 1  # 从服务器取回的结果条数
username = 'lskobeqq'
username_candidate_1 = 'lskobe'
username_candidate_2 = 'liushuaikobe'

# 缓存保存的位置
redis_addr = '127.0.0.1'
redis_port = 6379
redis_prefix = 'gitradar'
redis_count_prefix = 'grcount'
redis_info_prefix = 'grinfo'

# 日志的位置
log_file_name = '.'.join(('log', datetime.datetime.now().strftime('%Y%m%d'), 'txt'))
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file_name)


# 数据保存的位置
# data_base = '/root/data'
# data_base = '/home/footoo/githubradar/data'
data_base = '/Users/liushuai/Downloads/gitradar/data'

# location搜索索引保存位置
# ix_path = '/root/index'
ix_path = '/Users/liushuai/Downloads/gitradar/index'

# 各个地区用户数量的CSV文件的位置
# csv_path = '/root'
csv_path = '/Users/liushuai/Downloads/gitradar'

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
