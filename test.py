import re
import requests
import MySQLdb
import sys


pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')


def get_location_from_page(login):
    r = requests.get(''.join(('https://github.com/', login)))
    location = re.findall(pattern, r.text) if r.status_code != 404 else None
    return location[0].encode('utf-8') if location else None

def mysql_escape(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return MySQLdb.escape_string(s)


def test1():
    while True:
        print mysql_escape(raw_input())

if __name__ == '__main__':
    test1()

