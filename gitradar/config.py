# -*- coding: utf-8 -*-
from tornado.options import define

define('debug', default=False, type=bool)

# Tornado的监听端口
define('port', default=8888, type=int)

# WHoosh Search相关
define('whoosh_ix_path', default='/Users/liushuai/Desktop/index', type=str)

# MongoDB
define('mongo_addr', default='127.0.0.1', type=str)
define('mongo_port', default=27017, type=int)
