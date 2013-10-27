from gevent import monkey
monkey.patch_all()
import ujson
import gzip
import requests
import sys
import os
import time
from pymongo import MongoClient

client = MongoClient('localhost', 27017)

def task(r):
    pass

def clean(rl):
    filter(lambda )


def main(p):
    start = time.time()

    # Choose files ends with 'json.gz'
    file_name_list = filter(lambda x: x.endswith('json.gz'), os.listdir(p))


    end = time.time()



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)
    main(sys.argv[1])