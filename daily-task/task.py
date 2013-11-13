# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:15:37

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 14:16:16
'''
from gevent import monkey
monkey.patch_all()
import gevent
import gzip
import sys
import os
import time
import config
import utils
import log
import downloader
from cleaner import Cleaner
from pymongo import MongoClient


client = MongoClient(config.db_addr, config.db_port)

record_actor_exist = [] # Actor已经存在的记录
record_actor_new = [] # Actor之前不存在的记录，可能是该用户最近添加了location信息等等

actor_val_cache = {} # 在内存中缓存当天记录中各个actor新增的value，最后统一更新到数据库中
new_actor_cache = {} # 对于那些今日新增的Actor，可以在内存中计算完他们今天的val之后统一更新到DB中，以减少DB操作次数

trick_actor = [] # 那些location不准确的用户，例如：“/dev/null”,“The earth”


def actor_exist_dividing(records):
    """根据记录的actor是否存在把记录分成两组"""
    all_logins = [record['actor_attributes']['login'] for record in records]
    # 去重
    all_logins = {}.fromkeys(all_logins).keys()
    result = client[config.db].actor.find({"login": {"$in": all_logins}}, {"login": 1})
    exist_actors = [r['login'] for r in result]
    if not exist_actors:
        record_actor_new.extend(records)
        return
    for record in records:
        if record['actor_attributes']['login'] in exist_actors:
            record_actor_exist.append(record)
        else:
            record_actor_new.append(record)


def process_location_task(record):
    """对每个Actor进行地名的处理，本方法应该只应用于当日新增Actor的记录"""
    actor = record['actor']
    # 之前已经对这个用户进行过location的规范化了
    if actor in new_actor_cache or actor in trick_actor:
        # 只需要删掉这条记录的actor_attributes，等待后续处理
        del record['actor_attributes']
        return 
    # 之前没有对这个用户进行location的规范化
    else:
        attrs = record['actor_attributes']
        location = attrs['location']
        regular_location = utils.search_geo(location)
        if regular_location == None:
            # 把该用户加入到trick_actor
            trick_actor.append(actor)
        else:
            regular_location['origin'] = location
            attrs['location'] = regular_location
            # 把该用户添加到new_actor_cache
            new_actor_cache[actor] = attrs
        # 删掉记录的actor_attributes
        del record['actor_attributes']


def insert_new_actor_task(records):
    """将今日新增的actor插入数据库，应该进行bulk insert以提高效率"""
    client[config.db].actor.insert(records)


def process_val(records):
    """计算records中每条行为的价值，更新到内存中的缓存"""
    for record in records:
        actor = record['actor']
        if actor in actor_val_cache:
            actor_val_cache[actor] += calc_record_val(record)
        else:
            actor_val_cache[actor] = calc_record_val(record)


def insert_new_records_task(records):
    """将今日的所有记录插入数据库，应该进行bulk insert以提高效率"""
    client[config.db].event.insert(records)


def update_val_task(actor_val):
    """将今日所有用户新增加的分数更新到数据库中"""
    for actor in actor_val:
        client[config.db].actor.update({"login": actor}, {"$inc": {"val": actor_val[actor]}})


def clear_cache():
    """清空缓存"""
    record_actor_exist[:] = []
    record_actor_new[:] = []
    actor_val_cache.clear()
    new_actor_cache.clear()


def main(p):
    global record_actor_new, record_actor_exist
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
            log.log('Data cleaning...')
            record_cleaner.set_dirty_data(raw_json_file)
            record_cleaner.clean()
            clean_record = record_cleaner.get_clean_data()
            log.log('cleaning finished.')

            # 数据处理

            # 分组
            log.log('Data grouping...')
            while len(clean_record) >= 1000:
                actor_exist_dividing(clean_record[:1000])
                del clean_record[:1000]
            if clean_record:
                actor_exist_dividing(clean_record)
                del clean_record
            log.log('Grouping finished.')


            # 处理记录的actor已存在的记录
            log.log('Begin processing actor-exist records... %s total.' % len(record_actor_exist))
            # 只需要删掉记录的actor_attrs即可
            for record in record_actor_exist:
                del record['actor_attributes']
            log.log('Finished.')


            # 处理记录的actor不存在的记录
            log.log('Begin processing new-actor records... %s total.' % len(record_actor_new))
            # 处理location息，因为要进行网络连接，因此要控制每次处理的记录数量
            i = 0
            while i < len(record_actor_new):
                utils.set_alarm() # 设置警报
                jobs = [gevent.spawn(process_location_task, record) for record in record_actor_new[i:i+greenlet_num]]
                gevent.joinall(jobs)
                i += greenlet_num
                log.log('%s%% finished' % ((float(i) / float(len(record_actor_new))) * 100.0))


            # 对那些actor是trick_actor的记录，要删掉
            record_actor_new = filter(lambda x: x['actor'] not in trick_actor, record_actor_new)

            # 把本地的今日新增的Actor更新到数据库
            bulk_num = 1000
            log.log('Insert new actor of today...%s total.' % len(new_actor_cache))
            actors = [new_actor_cache[actor] for actor in new_actor_cache]
            jobs = [gevent.spawn(insert_new_actor_task, actors[i:i+bulk_num]) for i in range(0, len(actors), bulk_num)]
            gevent.joinall(jobs)
            log.log('Finished.')

            # 计算每条记录的val
            log.log('Calc the val of each records...')
            process_val(record_actor_exist)
            process_val(record_actor_new)
            log.log('Finished.')

            # 删除每条记录的payload
            # for record in record_actor_new:
            #     del record['payload']
            # for record in record_actor_exist:
            #     del record['payload']

            # 将记录插入数据库
            log.log('Insert all records into DB...')
            jobs = [gevent.spawn(insert_new_records_task, record_actor_new[i:i+bulk_num]) for i in \
                                                                    range(0, len(record_actor_new), bulk_num)]
            gevent.joinall(jobs)
            jobs = [gevent.spawn(insert_new_records_task, record_actor_exist[i:i+bulk_num]) for i in \
                                                                    range(0, len(record_actor_exist), bulk_num)]
            gevent.joinall(jobs)
            log.log('Finished.')

            # 将今日用户新增的val更新到数据库
            log.log('Update the added value of each user...')
            update_val_task(actor_val_cache)
            log.log('Finished.')

            # 清除缓存，准备处理下一个文件
            log.log('Clear cache...')
            clear_cache()
            log.log('Finished.')

    # 将地名缓存持久化
    utils.cache_persistence(utils.location_cache)

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