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
    con.connect('localhost', 3306, 'root', 'lskobe', 'gitarchive', True)

    # build location_sql
    safe_countryName = format_utf8(mysql_escape(regular_location['countryName']))
    safe_name = format_utf8(mysql_escape(regular_location['name']))
    safe_lat = format_utf8(regular_location['lat'])
    sage_lng = format_utf8(regular_location['lng'])

    location_sql = ' '.join((
            '''insert into Location (country, name, lat, lng)''',
            '''values ('%s', '%s', '%s', '%s')''' % (safe_countryName, safe_name, safe_lat, sage_lng),
            '''on duplicate key update''',
            '''country=values(country), lat=values(lat), lng=values(lng);'''
        ))
    con.query('START TRANSACTION;')
    con.query(location_sql)
    con.query('COMMIT;')

    # build actor_sql
    safe_location = format_utf8(attrs['location'])
    safe_login = format_utf8(attrs['login'])
    safe_email = format_utf8(attrs.get('email', ''))
    safe_type = format_utf8(attrs['type'])
    safe_name = format_utf8(attrs.get('name', ''))
    safe_blog = format_utf8(attrs.get('blog', ''))
    safe_regular_location = format_utf8(regular_location['name'])
        
    actor_sql = ' '.join((
            '''insert into Actor (location, login, email, type, name, blog, regular_location)''',
            '''select '%s', '%s', '%s', '%s', '%s', '%s', _id''' % (safe_location, safe_login, safe_email, safe_type, safe_name, safe_blog),
            '''from Location''',
            '''where name = '%s' ''' % (safe_regular_location),
            '''limit 1''',
            '''on duplicate key update''',
            '''location=values(location), email=values(email), type=values(type), name=values(name), blog=values(blog), regular_location=values(regular_location);'''
        ))
    con.query('START TRANSACTION;')
    con.query(actor_sql)
    con.query('COMMIT;')

    # build repo info
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

    repo_sql = ' '.join((
            '''insert into Repo (name, owner, language, url, description, forks, stars, create_at, push_at, id, watchers, private)''',
            '''values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')''' % (safe_name, safe_owner, safe_language, safe_url, safe_description, safe_forks, safe_stars, safe_created_at, safe_pushed_at, safe_id, safe_watchers, safe_private),
            '''on duplicate key update''',
            '''name=values(name), owner=values(owner), language=values(language), url=values(url), description=values(description), forks=values(forks), stars=values(stars), create_at=values(create_at), push_at=values(push_at), watchers=values(watchers), private=values(private);''',
        ))
    con.query('START TRANSACTION;')
    con.query(repo_sql)
    con.query('COMMIT;')

    # build event_sql
    safe_url = format_utf8(record['url'])
    safe_type = format_utf8(record['type'])
    safe_created_at = format_utf8(parse_iso8601(record['created_at']))
    safe_id = format_utf8(repo['id'])
    safe_actor = format_utf8(record['actor'])

    event_sql = '\n'.join((
            '''insert into Event (url, type, created_at, actor, repo)''',
            '''select '%s', '%s', '%s', _id, (select _id from Repo where id='%s' limit 1)''' % (safe_url, safe_type, safe_created_at, safe_id),
            '''from Actor where login='%s' limit 1;''' % (safe_actor),
        ))
    con.query('START TRANSACTION;')
    con.query(event_sql)
    con.query('COMMIT;')

    # insert this event
    # sql = ' '.join((location_sql, actor_sql, repo_sql, event_sql))
    # con.query(sql)


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
    # insert_serial(file_name_list)
    insert_parallel(file_name_list)

    end = time.time()
    output_observe_data(end - start)

if __name__ == '__main__':
    main()
