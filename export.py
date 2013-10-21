import simplejson
import threading
import gzip
import sys
import os
import time
from pymongo import MongoClient


DB_ADDRESS = 'localhost'
DB_PORT = 30000
THREAD_NUM = 15

#client = MongoClient(DB_ADDRESS, DB_PORT)
#db = client.testbig
#collection = db['201309']


class MyThread(threading.Thread):
    def __init__(self, thread_no, basepath, *gzfile):
        threading.Thread.__init__(self)
        self.thread_no = thread_no
        self.basepath = basepath
        self.gzfile = gzfile

        self.client = MongoClient(DB_ADDRESS, DB_PORT)
        self.db = self.client.testbig
        self.collection = self.db['sep']

        self.file_cnt = 0
        self.line_cnt = 0

    def run(self):
        total = len(self.gzfile)
        print 'Thread %s: %s - %s, %s files.' % (self.thread_no, self.gzfile[0], self.gzfile[total - 1], total)
        for filename in self.gzfile:
            self.file_cnt += 1
            with open(os.path.join(self.basepath, filename), 'r') as f:
                for i, line in enumerate(gzip.GzipFile(fileobj=f)):
                    try:
                        self.line_cnt += 1
                        line = line.decode('utf-8', 'ignore')
                        document = simplejson.loads(line)
                        self.collection.insert(document)
                    except Exception, e:
                        print 'FAILED: ', filename, i
                        print e.message
        print 'Thread %s Finished. %s files completed, %s documents inserted.' % (self.thread_no, self.file_cnt, self.line_cnt)


def main():
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)
    try:
        file_name_list = os.listdir(sys.argv[1])
        # Choose files ends with 'json.gz'
        file_name_list = filter(lambda x: x.endswith('json.gz'), file_name_list)
        total_num = len(file_name_list)
        print 'total: ', total_num
        task_num = total_num / THREAD_NUM
        threads = []
        for i in range(THREAD_NUM):
            if i == THREAD_NUM - 1:
                tmp = file_name_list
            else:
                tmp = file_name_list[:task_num]
            thread = MyThread(i, sys.argv[1], *tuple(tmp))
            del file_name_list[:task_num]
            threads.append(thread)

        start = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        end = time.time()

        print 'total time:', end - start

    except Exception, e:
        print e.message

if __name__ == '__main__':
    main()