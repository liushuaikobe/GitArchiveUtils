# -*- coding: utf-8 -*-
import os

from tornado.web import Application
from tornado.options import options, parse_config_file
from tornado.ioloop import IOLoop
import motor
from whoosh.index import open_dir

from handlers.index import IndexHandler
from handlers.report import ReportHandler
from handlers.rank import RankHandler


parse_config_file('config.py')

db = motor.MotorClient('162.243.37.124', 27017).open_sync().op_test
ix = open_dir('/Users/liushuai/Desktop/index')


handlers = [
    (r'/', IndexHandler),
    (r'/report/([A-Za-z0-9]+)', ReportHandler),
    (r'/rank/(.*)', RankHandler)
]

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
    'db': db,
    'ix': ix
}

application = Application(handlers, **settings)

if __name__ == '__main__':
    application.listen(options.port)
    IOLoop.instance().start()