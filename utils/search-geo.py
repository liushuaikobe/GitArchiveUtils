import sys
import requests
import simplejson

def search(q):
    params = {'q':q, 'maxRows':10, 'username':'liushuaikobe'}
    r = requests.get('http://api.geonames.org/searchJSON', params=params)
    # print r.url
    for e in simplejson.loads(r.text)['geonames']:
        for i in e:
            print i, '=>', e[i]
        break

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage : $python search-geo.py location-name'
        sys.exit(1)
    search(sys.argv[1])