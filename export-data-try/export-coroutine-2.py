from gevent import monkey
monkey.patch_all()
from pymongo import MongoClient
import simplejson
import sys
import gevent
import time
import gzip
import os


DB_ADDRESS = 'localhost'
DB_PORT = 27017

client = MongoClient(DB_ADDRESS, DB_PORT)
db = client.testbigfoo
collection = db.bar


def worker(base, file_name):
    with open(os.path.join(base, file_name), 'r') as f:
        for record in gzip.GzipFile(fileobj=f):
            collection.insert(simplejson.loads(record))
    print 'finish =>', file_name


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

    jobs = [gevent.spawn(worker, sys.argv[1], file_name) for file_name in file_name_list]
    gevent.joinall(jobs)

    end = time.time()
    print 'total time:', end - start


if __name__ == '__main__':
    main()