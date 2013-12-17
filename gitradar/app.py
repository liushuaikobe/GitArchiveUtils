# -*- coding: utf-8 -*-
from tornado.web import Application
from tornado.options import options, parse_config_file
from tornado.ioloop import IOLoop
import motor
import os
from handlers.index import IndexHandler
from handlers.report import ReportHandler


parse_config_file('config.py')
db = motor.MotorClient('172.16.0.1', 27017).open_sync().op_test

handlers = [
    (r'/', IndexHandler),
    (r'/report/([A-Za-z0-9]+)', ReportHandler)
]

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
    'db': db
}

application = Application(handlers, **settings)

if __name__ == '__main__':
    application.listen(options.port)
    IOLoop.instance().start()