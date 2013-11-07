# -*- coding: utf-8 -*-
from tornado.web import RequestHandler
from tornado.web import asynchronous
from tornado import gen
import motor


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
    def get(self, actor):
        result = yield motor.Op(self.settings['db'].event.group, 
                key={"repository.id": True},
                condition={"actor": actor},
                initial={"contribution": []},
                reduce=self.group_reduce
            )
        self.render('report.html', actor=actor, result=result)
        
