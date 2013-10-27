# -*- coding: utf-8 -*- 
from gevent import monkey
monkey.patch_socket()
import gevent
import umysql
import ujson
import gzip
import requests
import re
import sys
import os
import traceback
import time
import dateutil.parser
import MySQLdb


pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')

cache = {}

cache_hit = 0
search_times = 0


def task(record):
    record = ujson.loads(record)
    if record['type'] not in ['IssuesEvent', 'PullRequestEvent', 'PushEvent']:
        return
    actor = record.get('actor', '')
    attrs = record.get('actor_attributes', {})
    # an anonymous event (like a gist event) or an organization event
    if actor == '' or attrs.get('type') != 'User':
        return

    # handle location info
    if 'location' not in attrs:
        # Maybe this guy add his location info recently.
        # location = get_location_from_page(actor)
        # if not location:
        #     return
        return
    else:
        location = attrs['location']

    regular_location = search_geo(location)

    if not regular_location:
        return

    # A separate connection object per green thread or real thread
    con = umysql.Connection()
    con.connect('localhost', 3306, 'root', 'lskobe', 'gitarchive')

    safe_regular_location = _safe(regular_location['name'])
    search_sql = "select count(*) from Location where name='%s'" % (safe_regular_location)
    r = con.query(search_sql)
    if r.rows[0][0] == 0:
        insert_location_sql = "insert into Location (country, name, lat, lng) \
                                values ('%s', '%s', %s, %s)" % \
                                (_safe(regular_location['countryName']), safe_regular_location, _safe(regular_location['lat']), _safe(regular_location['lng']))
        con.query(insert_location_sql)
    else:
        update_location_sql = "update Location set country='%s', lat=%s, lng=%s where name='%s'" % \
                                (_safe(regular_location['countryName']), _safe(regular_location['lat']), _safe(regular_location['lng']), safe_regular_location)
        con.query(update_location_sql)

    safe_actor = _safe(attrs['login'])
    search_location_sql = "select _id from Location where name='%s'" % safe_regular_location
    r = con.query(search_location_sql)
    _id = r.rows[0][0]
    search_actor_sql = "select count(*) from Actor where login='%s'" % safe_actor
    r = con.query(search_actor_sql)
    if r.rows[0][0] == 0:
        insert_actor_sql = "insert into Actor (location, login, email, name, blog, regular_location) \
                                values ('%s', '%s', '%s', '%s', '%s', %s)" % \
                                (_safe(attrs['location']), safe_actor, _safe(attrs.get('email', '')), _safe(attrs.get('name', '')), _safe(attrs.get('blog', '')), _id)
        con.query(insert_actor_sql)
    else:
        update_actor_sql = "update Actor set location='%s', email='%s', name='%s', blog='%s', regular_location=%s where login='%s'" % \
                                (_safe(attrs['location']), _safe(attrs.get('email', '')), _safe(attrs.get('name', '')), _safe(attrs.get('blog', '')), _id, safe_actor)
        con.query(update_actor_sql)

    repo = record['repository']
    search_repo_sql = "select count(*) from Repo where id='%s'" % _safe(repo['id'])
    r = con.query(search_repo_sql)
    safe_id = _safe(repo['id'])
    if r.rows[0][0] == 0:
        insert_repo_sql = "insert into Repo (name, owner, language, url, description, forks, stars, create_at, push_at, id, watchers, private) \
                            values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                            (_safe(repo['name']), _safe(repo['owner']), _safe(repo.get('language', '')), _safe(repo['url']), _safe(repo.get('description', '')), 
                                _safe(repo['forks']), _safe(repo['stargazers']), _safe(parse_iso8601(repo['created_at'])), 
                                _safe(parse_iso8601(repo['pushed_at'])), safe_id, _safe(repo['watchers']), _safe(repo['private']))
        con.query(insert_repo_sql)
    else:
        update_repo_sql = "update Repo set name='%s', owner='%s', language='%s', url='%s', description='%s', forks='%s', stars='%s', create_at='%s', \
                                push_at='%s', watchers='%s', private='%s' where id='%s'" % \
                                (_safe(repo['name']), _safe(repo['owner']), _safe(repo.get('language', '')), _safe(repo['url']), _safe(repo.get('description', '')), 
                                _safe(repo['forks']), _safe(repo['stargazers']), _safe(parse_iso8601(repo['created_at'])),
                                _safe(parse_iso8601(repo['pushed_at'])), _safe(repo['watchers']), _safe(repo['private']), safe_id)
        con.query(update_repo_sql)

    search_actor_sql = "select _id from Actor where login='%s'" % _safe(actor)
    r = con.query(search_actor_sql)
    actor_id = r.rows[0][0] 

    search_repo_sql = "select _id from Repo where id='%s'" % _safe(repo['id'])
    r = con.query(search_repo_sql)
    repo_id = r.rows[0][0]
    insert_event_sql = "insert into Event (url, type, created_at, actor, repo) \
                            values ('%s', '%s', '%s', %s, %s)" % \
                            (_safe(record['url']), _safe(record['type']), _safe(parse_iso8601(record['created_at'])), actor_id, repo_id)
    con.query(insert_event_sql)


def get_location_from_page(login):
    r = requests.get(''.join(('https://github.com/', login)))
    location = re.findall(pattern, r.text) if r.status_code != 404 else None
    return location[0].encode('utf-8') if location else None


def search_geo(location):
    global search_times, cache_hit
    search_times += 1
    if location.lower() in cache:
        cache_hit += 1
        return cache[location.lower()]
    params = {'maxRows': 10, 'username': 'liushuaikobe', 'q': location}
    r = requests.get('http://api.geonames.org/searchJSON', params=params)
    # use the top result of search
    try:
        e = ujson.loads(r.text)['geonames'][0]
    except (KeyError, IndexError):
        e = None
    if e:
        regular_location = {
        # Difference between 'toponymName' and 'name'
        # http://gis.stackexchange.com/questions/10054/difference-between-name-and-toponym-name
        'name': e['name'] if 'name' in e else e.get('toponymName', ''),
        'countryName': e['countryName'] if 'countryName' in e else e.get('countryCode', ''),
        'lat': e['lat'],
        'lng': e['lng']
        }
    else:
        regular_location = {}
    cache[location.lower()] = regular_location
    return regular_location

def parse_iso8601(t):
    return dateutil.parser.parse(t).strftime('%Y-%m-%d %H:%M:%S')


def mysql_escape(s):
    return MySQLdb.escape_string(s)


def format_utf8(s):
    return s.encode('utf-8') if isinstance(s, unicode) else s

def _safe(s):
    if isinstance(s, unicode):
        return mysql_escape(format_utf8(s))
    elif isinstance(s, str):
         return mysql_escape(s)
    else:
        return s


def insert_parallel(file_name_list, greenlet_num=90):
    print 'Total Json Files:', len(file_name_list)
    for file_name in file_name_list:
        with open(os.path.join(sys.argv[1], file_name), 'r') as f:
            all_lines = [line for line in gzip.GzipFile(fileobj=f)]
            print 'Processing {0}, {1} lines.'.format(file_name, str(len(all_lines)))
            while len(all_lines) >= greenlet_num:
                jobs = [gevent.spawn(task, line) for line in all_lines[:greenlet_num]]
                gevent.joinall(jobs)
                del all_lines[:greenlet_num]
            if all_lines:
                jobs = [gevent.spawn(task, line) for line in all_lines]
                gevent.joinall(jobs)
        print 'Finish =>', file_name

def insert_serial(file_name_list):
    print 'Total Json Files:', len(file_name_list)
    for file_name in file_name_list:
        with open(os.path.join(sys.argv[1], file_name), 'r') as f:
            all_lines = [line for line in gzip.GzipFile(fileobj=f)]
            print 'Processing {0}, {1} lines.'.format(file_name, str(len(all_lines)))
            for line in all_lines:
                task(line)
        print 'Finish =>', file_name

def output_observe_data(t):
    print '*' * 80
    print 'Total Time(s):', t
    print 'Cache Num:', len(cache)
    print 'Total Internet Requests:', search_times
    print 'Cache Hit:', cache_hit
    print '*' * 80

def main():
    if len(sys.argv) < 2:
       print 'Give me the json file path.'
       sys.exit(1)

    # Choose files ends with 'json.gz'
    file_name_list = filter(lambda x: x.endswith('json.gz'), os.listdir(sys.argv[1]))

    start = time.time()

    # task begins
    insert_serial(file_name_list)
    # insert_parallel(file_name_list)

    end = time.time()
    output_observe_data(end - start)

if __name__ == '__main__':
    main()
