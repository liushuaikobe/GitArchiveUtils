import re
import requests


pattern = re.compile(r'itemprop="homeLocation"><span class="octicon octicon-location"></span>(.+)</li>')


def get_location_from_page(login):
    r = requests.get(''.join(('https://github.com/', login)))
    location = re.findall(pattern, r.text) if r.status_code != 404 else None
    return location[0].encode('utf-8') if location else None


if __name__ == '__main__':
    print get_location_from_page('liushuaikobe')

