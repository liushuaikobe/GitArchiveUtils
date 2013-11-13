# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:15:45

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 15:04:13
'''
import config
import ujson
import decorator


class Cleaner(object):
    """数据清洗器，对一个Json文件做清洗"""
    def __init__(self, dirty_json_file=None):
        self.clean_data = [] # 保存清洗之后的数据
        self.dirty_json_file = dirty_json_file # 要被清洗的文件

    @decorator.log('Data cleaning...', 'Cleaning finished.')
    def clean(self, extra_filter=None):
        """把record转成dict并进行清洗"""
        dirty_lines = [ujson.loads(line.decode('utf-8', 'ignore')) for line in self.dirty_json_file]
        # 找出能被称之为“贡献”的记录
        dirty_lines = filter(lambda x: x.get('type', '') in config.contribution_type, dirty_lines)
        # 找出actor属性存在且actor_attributes存在的记录（确保是真实的人而不是组织或者其他）
        dirty_lines = filter(lambda x: x.get('actor', '').strip() \
            and x.get('actor_attributes', {}).get('type') == 'User', dirty_lines)
        # 找出actor_attributes中location属性存在的记录
        dirty_lines = filter(lambda x: 'location' in x['actor_attributes'] and \
            x['actor_attributes']['location'].strip(), dirty_lines)
        # 删除每条记录的payload属性
        for line in dirty_lines:
            del line['payload']

        # 自定义清洗条件
        if extra_filter and callable(extra_filter):
            dirty_lines = filter(extra_filter, dirty_lines)

        self.clean_data = dirty_lines

    def set_dirty_data(self, f):
        self.dirty_json_file = f

    def get_clean_data(self):
        return self.clean_data

