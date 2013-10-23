from gevent import monkey
monkey.patch_all()
import gevent
import umysql
import ujson
import gzip
import requests
import re
import sys
import os
import time


con = umysql.Connection()
con.connect('localhost', 3306, 'root', 'lskobe', 'gitarchive')

pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')

cache = {}

cache_hit = 0
search_times = 0


def task(record):
    record = ujson.loads(record)
    actor = record['actor']
    attrs = record.get("actor_attributes", {})
    # an anonymous event (like a gist event) or an organization event
    if actor is None or attrs.get('type') != 'User':
        return

    # handle location info
    if 'location' not in attrs:
        # Maybe this guy add his location info recently.
        location = get_location_from_page(actor)
        if not location:
            return
    else:
        location = attrs['location']

    regular_location = search_geo(location)

    if not regular_location:
        return

    location_sql = '''
        insert into Location (country, name, lat, lng)
        values (%s, %s, %s, %s)
        on duplicate key update
        country=values(country), lat=values(lat), lng=values(lng)
    ''' % (regular_location['countryName'], regular_location['name'], regular_location['lat'], regular_location['lng'])
    print location_sql
    con.query(location_sql)

    # handle actor info
    actor_sql = '''
        insert into Actor (location, login, email, type, name, blog, regular_location)
        select '%s', '%s', '%s', '%s', '%s', '%s', _id
        from Location
        where name = '%s'
        limit 1
        on duplicate key update
        location=values(location), email=values(email), type=values(type), name=values(name), blog=values(blog), regular_location=values(_id)
    ''' % (attrs['location'], attrs['login'], attrs['email'], attrs['type'], attrs['name'], attrs.get('blog', ''), regular_location['name'])
    con.query(actor_sql)

    # handle repo info
    repo = record['repository']
    repo_sql = '''
        insert into Repo (name, owner, language, url, description, forks, stars, create_at, push_at, id, watchers, private)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        on duplicate key update
        name=values(name), owner=values(owner), language=values(language), url=values(url), description=values(description), forks=values(forks), stars=values(stars), create_at=values(create_at), push_at=values(push_at), watchers=values(watchers), private=values(private)
    ''' % (repo['name'], repo['owner'], repo['language'], repo['url'], repo['description'], repo['forks'], repo['stargazers'], repo['created_at'], repo['pushed_at'], repo['id'], repo['watchers'], repo['private'])
    con.query(repo_sql)

    # insert this event
    event_sql = '''
        insert into Event (url, type, created_at, actor, repo)
        values(%s, %s, %s, (select _id from Actor where login=%s limit 1), (select _id from Repo where id=%s limit 1))
    ''' % (record['url'], record['type'], record['created_at'], record['actor'], repo['id'])
    con.query(event_sql)


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


def main():
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)

    file_name_list = os.listdir(sys.argv[1])
    # Choose files ends with 'json.gz'
    file_name_list = filter(lambda x: x.endswith('json.gz'), file_name_list)
    total_num = len(file_name_list)
    print 'total: ', total_num

    start = time.time()

    for file_name in file_name_list:
        with open(os.path.join(sys.argv[1],file_name), 'r') as f:
            jobs = [gevent.spawn(task, line) for line in gzip.GzipFile(fileobj=f)]
            gevent.joinall(jobs)

    end = time.time()
    print 'total time:', end - start

if __name__ == '__main__':
    main()
