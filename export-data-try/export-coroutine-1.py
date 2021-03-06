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


def worker(record):
    client.testbigfoo.bar.insert(simplejson.loads(record))


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
            jobs = [gevent.spawn(worker, line) for line in gzip.GzipFile(fileobj=f)]
            gevent.joinall(jobs)
            print 'finish =>', file_name

    end = time.time()
    print 'total time:', end - start


if __name__ == '__main__':
    main()