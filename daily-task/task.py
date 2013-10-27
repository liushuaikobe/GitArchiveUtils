# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()
import ujson
import gzip
import requests
import sys
import os
import time
import config
from cleaner import Cleaner
from pymongo import MongoClient

client = MongoClient(config.db_addr, config.db_port)

record_actor_exist = [] # Actor已经存在的记录
record_actor_new = [] # Actor之前不存在的记录，可能是该用户最近添加了location信息等等


def actor_exist_dividing(records):
    """根据记录的actor是否存在把记录分成两组"""
    all_logins = [record['actor_attributes']['login'] for record in records]
    # 去重
    all_logins = {}.fromkeys(all_logins).keys()
    result = client[config.db].actor.find({"login": {"$in": all_logins}}, {"login": 1})
    if not result:
        record_actor_new.append(records)
        return
    exist_actors = [r['login'].encode('utf-8') for r in result]
    for record in records:
        if record['actor_attributes']['login'] in exist_actors:
            record_actor_exist.append(record)
        else:
            record_actor_new.append(record)


def calc_record_val(record):
    """计算一条贡献的价值"""
    return 0


def main(p):
    start = time.time()

    # 选择文件名以'json.gz'结尾的记录
    file_name_list = filter(lambda x: x.endswith('json.gz'), os.listdir(p))

    # TODO 添加文件是否是24个的判断(glob模块)

    record_cleaner = Cleaner()
    greenlet_num = config.greenlet_num

    for file_name in file_name_list:
        with open(os.path.join(p, file_name), 'r') as f:
            raw_json_file = gzip.GzipFile(fileobj=f)
            # 数据清洗
            record_cleaner.set_dirty_data(raw_json_file)
            record_cleaner.clean()
            clean_record = record_cleaner.get_clean_data()
            # 数据处理
            # 分组
            while len(clean_record) >= 1000:
                actor_exist_dividing(clean_record[:1000])
                del clean_record[:1000]
            if clean_record:
                actor_exist_dividing(clean_record)
                del clean_record
            # 处理记录的actor之前已存在的记录

            # 处理记录的actor之前不存在的记录




    end = time.time()



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Give me the json file path.'
        sys.exit(1)
    main(sys.argv[1])