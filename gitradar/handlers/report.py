# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen
import motor

from business import util


class ReportHandler(RequestHandler):
    """生成用户个人报告"""
    def initialize(self):
        self.group_reduce = '''
            function (doc, prev) {
                for (var i = 0; i < prev["contribution"].length; i++) {
                    var e = prev["contribution"][i];
                    if (e["name"] === doc.repository.name && e["star"] === doc.repository.stargazers && e["fork"] === doc.repository.forks) {
                        if (doc.type in e["payload"]) {
                            e["payload"][doc.type]++;
                        } else {
                            e["payload"][doc.type] = 1;
                        }
                        return ;
                    } 
                }
                var n = {
                    "name": doc.repository.name,
                    "star": doc.repository.stargazers,
                    "fork": doc.repository.forks,
                    "url": doc.repository.url,
                    "payload": {}
                }
                n["payload"][doc.type] = 1;
                prev["contribution"].push(n);  
        }
        '''

    @asynchronous
    @gen.coroutine
    def get(self, actor_login):
        # 检索出用户的全部信息
        actor_vivid = yield motor.Op(self.settings['db'].actor.find_one, {'login': actor_login})
        # 检索出用户最近一周致力于哪些repos
        cursor = self.settings['db'].event.find({'created_at': {'$gt': util.a_week_ago_iso()}}).sort({'created_at': 1})
        recently_devoted_repos = []
        recently_devoted_repos_url = []
        n = 3 # 找到3个即可
        while (yield cursor.fetch_next):
            event = cursor.next_object()
            repo = event['repository']
            if repo['fork'] == True or repo['name'] in recently_devoted_repos:
                continue
            recently_devoted_repos.append(repo['name'])
            recently_devoted_repos_url.append(repo['url'])
            if len(recently_devoted_repos) == n:
                break

        result = yield motor.Op(self.settings['db'].event.group, 
                key={"repository.id": True},
                condition={"actor": actor_login},
                initial={"contribution": []},
                reduce=self.group_reduce
            )
        self.render('report.html', actor=actor_vivid, result=result)
        
