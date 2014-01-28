# -*- coding: utf-8 -*-
import datetime


def get_now_iso():
    '''获取当前ISO8601的时间'''
    return datetime.datetime.now().isoformat()


def a_week_ago_iso():
    today = datetime.datetime.today()
    a_week_delta = datetime.timedelta(weeks=1)
    a_week_ago = today - a_week_delta
    return a_week_ago.isoformat()


# only for test
if __name__ == '__main__':
    print get_now_iso()
    print a_week_ago_iso()
