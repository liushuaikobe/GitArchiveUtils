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
        cursor = self.settings['db'].event.find({'actor': actor_login}).sort([('created_at', -1)])
        # cursor = self.settings['db'].event.find({'created_at': {'$gt': util.a_week_ago_iso()}, 'actor': actor_login})
        # .sort([('created_at', -1)])

        recently_devoted_repos = {} 
        most_popular_repo_id = ''
        max_concerns = -1 # 记录这些repo中哪个最流行

        recently_devoted_os_repos = {}
        most_popular_os_repos_id = ''
        event_type_count = {
                'IssuesEvent': 0,
                'PullRequestEvent': 0,
                'PushEvent': 0
                }
        max_os_concerns = -1 # 记录贡献过的开源项目哪个最流行

        while (yield cursor.fetch_next):
            event = cursor.next_object()
            repo = event['repository']

            if repo['owner'] != actor_login: # 为开源项目做的贡献
                if repo['id'] not in recently_devoted_os_repos:
                    recently_devoted_os_repos[repo['id']] = {
                                'owner': repo['owner'],
                                'name': repo['name'],
                                'forks': repo['forks'],
                                'stargazers': repo['stargazers'],
                                'url': repo['url']
                            }
                    current_concerns = repo['stargazers'] + repo['forks']  
                    if current_concerns > max_os_concerns:
                        max_os_concerns = current_concerns
                        most_popular_os_repos_id = repo['id']
                event_type_count[event['type']] += 1
            else:
                if repo['id'] not in recently_devoted_repos:
                    recently_devoted_repos[repo['id']] = {
                                'owner': repo['owner'],
                                'name': repo['name'],
                                'forks': repo['forks'],
                                'stargazers': repo['stargazers'],
                                'url': repo['url']
                            }
                    current_concerns = repo['stargazers'] + repo['forks']
                    if current_concerns > max_concerns:
                        max_concerns = current_concerns
                        most_popular_repo_id = repo['id']

        result = yield motor.Op(self.settings['db'].event.group, 
                key={"repository.id": True},
                condition={"actor": actor_login},
                initial={"contribution": []},
                reduce=self.group_reduce
            )
        args = {
            'debug': True,
            'actor': actor_vivid,
            'result': result,
            'recently_devoted_repos': recently_devoted_repos,
            'most_popular_repo_id': most_popular_repo_id,
            'recently_devoted_os_repos': recently_devoted_os_repos,
            'most_popular_os_repos_id': most_popular_os_repos_id,
            'event_type_count': event_type_count,
            'event_total': sum(event_type_count.values()) 
        }
        self.render('report.html', **args)
        
