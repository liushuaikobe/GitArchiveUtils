# -*- coding: utf-8 -*-
import os

from tornado.web import Application
from tornado.options import options, parse_config_file
from tornado.ioloop import IOLoop
import motor
from whoosh.index import open_dir

from business.search import GRSearcher 
from handlers.search import SearchHandler
from handlers.visual import VisualHandler
from handlers.index import IndexHandler
from handlers.report import ReportHandler
from handlers.rank import RankHandler
from handlers.test import TestHandler


parse_config_file('config.py')

db = motor.MotorClient('162.243.37.124', 27017).open_sync().op_test
gr_searcher = GRSearcher(options.whoosh_ix_path)

handlers = [
    (r'/', IndexHandler),
    (r'/visual', VisualHandler),
    (r'/search/(.*)', SearchHandler),
    (r'/report/([A-Za-z0-9]+)', ReportHandler),
    (r'/rank/(.*)', RankHandler),
    # only for test
    (r'/test', TestHandler)
]

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'debug': True,
    'db': db,
    'searcher': gr_searcher 
}

application = Application(handlers, **settings)

if __name__ == '__main__':
    application.listen(options.port)
    IOLoop.instance().start()
