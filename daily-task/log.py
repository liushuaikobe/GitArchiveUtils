# -*- coding: utf-8 -*-
import os

import logging
import config


CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG

logging.basicConfig(filename=config.log_file, level = logging.DEBUG, \
    filemode = 'a+', format = '%(asctime)s - %(levelname)s: %(message)s')

# 禁用掉python的requests模块的默认日志
requests_log = logging.getLogger('requests')
requests_log.setLevel(logging.WARNING)


def log(msg, level=INFO):
    if level == DEBUG:
        logging.debug(msg)
    elif level == INFO:
        logging.info(msg)
    elif level == WARNING:
        logging.warning(msg)
    elif level == ERROR:
        logging.error(msg)
    elif level == CRITICAL:
        logging.critical(msg)