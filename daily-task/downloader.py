# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import os
import shutil
import datetime
from itertools import product
from tempfile import NamedTemporaryFile

import gevent
import requests

import config
import log
import util


yesterday = datetime.date.today() - datetime.timedelta(days=1)
year = yesterday.year
month = yesterday.month
day = yesterday.day

data_dir = os.path.join(config.data_base, str(year), str(month), str(day))
filename = os.path.join(data_dir, "{year}-{month:02d}-{day:02d}-{n}.json.gz")

try:
    os.makedirs(data_dir)
except os.error:
    pass

url = "http://data.githubarchive.org/{year}-{month:02d}-{day:02d}-{n}.json.gz"


def fetch(year, month, day, n):
    kwargs = {"year": year, "month": month, "day": day, "n": n}
    local_fn = filename.format(**kwargs)

    # Skip if the file exists.
    if os.path.exists(local_fn):
        return

    # Download the remote file.
    remote = url.format(**kwargs)
    r = requests.get(remote)
    if r.status_code == requests.codes.ok:
        # Atomically write to disk.
        # http://stackoverflow.com/questions/2333872/ \
        #        atomic-writing-to-file-with-python
        f = NamedTemporaryFile("wb", delete=False)
        f.write(r.content)
        f.flush()
        os.fsync(f.fileno())
        f.close()
        shutil.move(f.name, local_fn)
        log.log('Downloading {0}-{1:02d}-{2:02d}-{3}.json.gz finished.'.format(year, month, day, n))
    else:
        log.log('Fail downloading {0}-{1:02d}-{2:02d}-{3}.json.gz. ({4}).'.format(year, month, day, n, r.status_code), log.ERROR)


def fetch_yesterday():
    """下载昨日的数据"""
    jobs = [gevent.spawn(fetch, year, month, day, n)
            for n in range(24)]
    gevent.joinall(jobs)
    if not util.detect(data_dir, year, month, day):
        util.sendmail('Download Error', '\n'.join(os.listdir(data_dir)) + '\nFound In Target Dir.')

if __name__ == "__main__":
    fetch_yesterday()