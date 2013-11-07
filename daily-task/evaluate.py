# -*- coding: utf-8 -*-
import config


class Evaluater(object):
    """对一条记录做出价值评估"""
    def __init__(self):
        pass

    def calc_repo_val(self, repo):
    """计算一个repo的价值，计算方法：star数 * star权重 + fork数 * fork权重"""
        repo_stars = float(repo['stargazers'])
        repo_forks = float(repo['forks'])
        return repo_stars * config.weight['star'] + repo_forks * config.weight['fork']

    def evaluate(self, record):
    """评估一条记录的价值，评估方法：贡献类型基础值 + repo价值"""
        repo_val = self.calc_repo_val(record['repository']) if 'repository' in record else 0
        return config.credit[record['type']] + repo_val