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

    try:
        safe_countryName = format_utf8(mysql_escape(regular_location['countryName']))
        safe_name = format_utf8(mysql_escape(regular_location['name']))
        safe_lat = format_utf8(regular_location['lat'])
        sage_lng = format_utf8(regular_location['lng'])

        location_sql = '\
            insert into Location (country, name, lat, lng)\
            values ("%s", "%s", "%s", "%s")\
            on duplicate key update\
            country=values(country), lat=values(lat), lng=values(lng)\
        ' % (safe_countryName, safe_name, safe_lat, sage_lng)
        con.query(location_sql)
    except umysql.SQLError, e:
        print 'FAIL:\n', location_sql
        print e
        print traceback.format_exc()

    #handle actor info
    try:
        actor_sql = '\
            insert into Actor (location, login, email, type, name, blog, regular_location)\
            select "%s", "%s", "%s", "%s", "%s", "%s", _id\
            from Location\
            where name = "%s"\
            limit 1\
            on duplicate key update\
            location=values(location), email=values(email), type=values(type), name=values(name), blog=values(blog), regular_location=values(_id)\
        ' % (attrs['location'], attrs['login'], attrs.get('email', ''), attrs['type'], attrs.get('name', ''), attrs.get('blog', ''), regular_location['name'])
        con.query(actor_sql)
    except umysql.SQLError, e:
        print 'FAIL:\n', actor_sql
        print e
        print traceback.format_exc()
        foo = 'select _id from Location where name = "%s" limit 1' % regular_location['name'] 
        print '*' * 80
        print foo
        print '*' * 80
        result = con.query(foo)
        print result.rows
        print '*' * 80

    # handle repo info
    try:
        repo = record['repository']

        safe_name = format_utf8(repo['name'])
        safe_owner = format_utf8(repo['owner'])
        safe_language = format_utf8(repo.get('language', ''))
        safe_url = format_utf8(repo['url'])
        safe_description = format_utf8(mysql_escape(repo.get('description', '')))
        safe_forks = format_utf8(repo['forks'])
        safe_stars = format_utf8(repo['stargazers'])
        safe_created_at = format_utf8(parse_iso8601(repo['created_at']))
        safe_pushed_at = format_utf8(parse_iso8601(repo['pushed_at']))
        safe_id = format_utf8(repo['id'])
        safe_watchers = format_utf8(repo['watchers'])
        safe_private = format_utf8(repo['private'])

        repo_sql = "\
            insert into Repo (name, owner, language, url, description, forks, stars, create_at, push_at, id, watchers, private)\
            values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')\
            on duplicate key update\
            name=values(name), owner=values(owner), language=values(language), url=values(url), description=values(description), forks=values(forks), stars=values(stars), create_at=values(create_at), push_at=values(push_at), watchers=values(watchers), private=values(private)\
        " % (safe_name, safe_owner, safe_language, safe_url, safe_description, safe_forks, safe_stars, safe_created_at, safe_pushed_at, safe_id, safe_watchers, safe_private)
        con.query(repo_sql)
    except umysql.SQLError, e:
        print 'FAIL:\n', repo_sql
        print e
        print traceback.format_exc()
        print record['type']

    # insert this event
    try:
        safe_url = format_utf8(record['url'])
        safe_type = format_utf8(record['type'])
        safe_created_at = format_utf8(parse_iso8601(record['created_at']))
        safe_id = format_utf8(repo['id'])
        safe_actor = format_utf8(record['actor'])

        event_sql = "\
            insert into Event (url, type, created_at, actor, repo)\
            select '%s', '%s', '%s', _id, (select _id from Repo where id='%s' limit 1)\
            from Actor where login='%s' limit 1\
        " % (safe_url, safe_type, safe_created_at, safe_id, safe_actor)
        con.query(event_sql)
    except umysql.SQLError, e:
        print 'FAIL:\n', event_sql
        print e
        print traceback.format_exc()


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
    s = format_utf8(s)
    return MySQLdb.escape_string(s)


def format_utf8(s):
    return s.encode('utf-8') if isinstance(s, unicode) else s


def insert_parallel(file_name_list, greenlet_num=90):
    for file_name in file_name_list:
        with open(os.path.join(sys.argv[1], file_name), 'r') as f:
            all_lines = [line for line in gzip.GzipFile(fileobj=f)]
            while len(all_lines) >= greenlet_num:
                jobs = [gevent.spawn(task, line) for line in all_lines[:greenlet_num]]
                gevent.joinall(jobs)
                del all_lines[:greenlet_num]
            if all_lines:
                jobs = [gevent.spawn(task, line) for line in all_lines]
                gevent.joinall(jobs)

def insert_serial(file_name_list):
    for file_name in file_name_list:
        with open(os.path.join(sys.argv[1], file_name), 'r') as f:
            all_lines = [line for line in gzip.GzipFile(fileobj=f)]
            for line in all_lines:
                task(line)

def main():
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)

    # Choose files ends with 'json.gz'
    file_name_list = filter(lambda x: x.endswith('json.gz'), os.listdir(sys.argv[1]))
    total_num = len(file_name_list)
    print 'total: ', total_num

    start = time.time()


    insert_serial(file_name_list)

    end = time.time()
    print 'total time:', end - start

if __name__ == '__main__':
    main()
