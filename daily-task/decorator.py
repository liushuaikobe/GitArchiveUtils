# -*- coding: utf-8 -*-
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
