# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:38:43

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 14:58:34
'''
import log
import functools

def _log(before_msg, after_msg):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log.log(before_msg)
            r = func(*args, **kwargs)
            log.log(after_msg)
            return r
        return wrapper
    return actual_decorator
