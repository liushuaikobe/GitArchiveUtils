# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import gzip
import sys
import os
import time

import gevent
from pymongo import MongoClient

import config
import log
import downloader
import util
from cleaner import Cleaner
from group import Grouper
from normalize import Normalizer
from database import MongoHelper
from count import ActorCounter
from evaluate import Evaluater


client = MongoClient(config.db_addr, config.db_port)
db = client[config.db]

@profile
def main(p):
    start = time.time()

    # 选择文件名以'json.gz'结尾的记录
    file_name_list = filter(lambda x: x.endswith('json.gz'), os.listdir(p))

    # TODO 添加文件是否是24个的判断(glob模块)

    for file_name in file_name_list:
        with open(os.path.join(p, file_name), 'r') as f:
            raw_json_file = gzip.GzipFile(fileobj=f)

            record_cleaner = Cleaner()
            record_grouper = Grouper(db)
            record_normalizer = Normalizer(db)
            mongo_helper = MongoHelper(db)
            counter = ActorCounter()
            evaluater = Evaluater()

            # 数据清洗
            record_cleaner.set_dirty_data(raw_json_file)
            record_cleaner.clean()
            clean_record = record_cleaner.get_clean_data()
            log.log('clean record %s' % len(clean_record))
            # 数据处理

            # 分组
            record_grouper.set_records(clean_record)
            record_grouper.group()
            record_actor_exist = record_grouper.get_group_1()
            record_actor_new= record_grouper.get_group_2()
            log.log('record_actor_exist: %s' % len(record_actor_exist))
            log.log('record_actor_new: %s' % len(record_actor_new))


            # 处理记录的actor已存在的记录
            log.log('Begin processing actor-exist records...')
            # 只需要删掉记录的actor_attrs即可
            for record in record_actor_exist:
                del record['actor_attributes']
            log.log('Finished.')


            # 处理记录的actor不存在的记录
            record_normalizer.set_records(record_actor_new)
            record_normalizer.normalize()
            record_actor_new = record_normalizer.get_record_actor_new()
            new_actors = record_normalizer.get_new_actors()

            # 把本地的今日新增的Actor更新到数据库
            actors = new_actors.values()
            mongo_helper.insert_new_actors(actors)

            # 对新增的Actor, 改变Redis中相应的计数
            counter.count_actor_list(actors)

            # 计算每条记录的val
            evaluater.set_records(record_actor_exist)
            evaluater.evaluate()
            val_actor_exist = evaluater.get_val_cache()

            evaluater.set_records(record_actor_new)
            evaluater.evaluate()
            val_actor_new = evaluater.get_val_cache()

            # 将记录插入数据库
            mongo_helper.insert_new_reocrds(record_actor_new)
            mongo_helper.insert_new_reocrds(record_actor_exist)

            # 将今日用户新增的val更新到数据库
            mongo_helper.update_val(val_actor_new)
            mongo_helper.update_val(val_actor_exist)

            record_cleaner.free_mem()
            del record_cleaner
            del record_grouper
            del record_normalizer
            del mongo_helper
            del counter
            del evaluater

    # 生成CSV文件
    util.grcount2csv()

    end = time.time()
    log.log('total: %s s' % (end - start))


if __name__ == '__main__':
    if config.debug:
        if len(sys.argv) < 2:
            print 'Give me the json file path.'
            sys.exit(1)
        main(sys.argv[1])
    else:
        downloader.fetch_yesterday()
        main(downloader.data_dir)
