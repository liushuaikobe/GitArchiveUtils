# -*- coding: utf-8 -*-
'''
Created on 2013-11-13 14:17:33

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-13 14:17:40
'''
import config
import decorator


class Evaluater(object):
    """对一条记录做出价值评估"""
    def __init__(self):
        self.records = []
        self.actor_val_cache = {}

    def set_records(self, r):
        self.records = r

    def calc_repo_val(self, repo):
        """计算一个repo的价值，计算方法：star数 * star权重 + fork数 * fork权重"""
        repo_stars = float(repo['stargazers'])
        repo_forks = float(repo['forks'])
        return repo_stars * config.weight['star'] + repo_forks * config.weight['fork']

    def evaluate_a_record(self, record):
        """评估一条记录的价值，评估方法：贡献类型基础值 + repo价值"""
        repo_val = self.calc_repo_val(record['repository']) if 'repository' in record else 0
        return config.credit[record['type']] + repo_val

    @decorator._log('Calc the value of records...', 'Finished.')
    def evaluate(self):
        self.actor_val_cache.clear()
        for r in self.records:
            actor = r['actor']
            if actor in self.actor_val_cache:
                self.actor_val_cache[actor] += self.evaluate_a_record(r)
            else:
                self.actor_val_cache[actor] = self.evaluate_a_record(r)

    def get_val_cache(self):
        return self.actor_val_cache

