import re
import requests
import MySQLdb
import sys
import ujson

pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')


def get_location_from_page(login):
    r = requests.get(''.join(('https://github.com/', login)))
    location = re.findall(pattern, r.text) if r.status_code != 404 else None
    return location[0].encode('utf-8') if location else None

def mysql_escape(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return MySQLdb.escape_string(s)

def search_geo(location):
    global search_times, cache_hit
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
        'name': e['name'].encode('utf-8') if 'name' in e else e.get('toponymName', ''),
        'countryName': e['countryName'].encode('utf-8') if 'countryName' in e else e.get('countryCode', ''),
        'lat': e['lat'],
        'lng': e['lng']
        }
    else:
        regular_location = {}
    return regular_location

def test2():
    while True:
        print search_geo(raw_input())


def test1():
    while True:
        print mysql_escape(raw_input())

if __name__ == '__main__':
    test2()

