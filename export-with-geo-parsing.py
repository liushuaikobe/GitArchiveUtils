from gevent import monkey
monkey.patch_all()
import simplejson
import gzip
import requests
import sys
import os
import time
import re
import gevent
from pymongo import MongoClient


DB_ADDRESS = 'localhost'
DB_PORT = 27017

client = MongoClient(DB_ADDRESS, DB_PORT)
db = client.testbig
collection = db.bar

cache = {}

cache_hit = 0
search_times = 0

pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')


def worker(record):
    record = record.decode('utf-8', 'ignore')
    record = simplejson.loads(record)
    if record['type'] == 'GistEvent':
        return
    if 'actor_attributes' in record:
        if 'location' in record['actor_attributes']:
            location = record['actor_attributes']['location']
            print 'location already have =>', location
        # In case he add his location right now
        elif 'login' in record['actor_attributes']:
            login = record['actor_attributes']['login']
            r = requests.get(''.join(('https://github.com/', login)))
            location = re.findall(pattern, r.text) if r.status_code != 404 else None
            if location:
                location = location[0].encode('utf-8')
                print 'location get from page =>', location
        else:
            location = None
            print 'location N/A'
        if location:
            regular_location = search_geo(location)
            if regular_location:
                regular_location['origin'] = location
                record['actor_attributes']['location'] = regular_location
                # Save the record only if the location info exists
                collection.insert(record)


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
        e = simplejson.loads(r.text)['geonames'][0]
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
        cache[location.lower()] = regular_location
    else:
        regular_location = None
    return regular_location


def cache_persistence():
    cache_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache.txt')
    with open(cache_name, 'w') as f:
        f.write(str(cache))


def main():
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)
    try:
        #file_name_list = os.listdir(sys.argv[1])
        ## Choose files ends with 'json.gz'
        #file_name_list = filter(lambda x: x.endswith('json.gz'), file_name_list)
        #total_num = len(file_name_list)
        #print 'total: ', total_num

        start = time.time()
        print start
        jobs = [gevent.spawn(worker, line) for line in gzip.GzipFile(fileobj=open(sys.argv[1], 'r'))]
        gevent.joinall(jobs)
        print 'cache hit =>', cache_hit
        print 'total search times =>', search_times
        cache_persistence()
        end = time.time()
        print 'total time:', end - start

    except Exception, e:
        print e.message

if __name__ == '__main__':
    main()