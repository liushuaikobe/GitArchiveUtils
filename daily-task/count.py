# -*- coding: utf-8 -*-
import config
import decorator
from database import get_redis_pipeline


class Counter(object):
    """Redis计数器"""
    def __init__(self, prefix=config.redis_count_prefix):
        self.pipe = get_redis_pipeline()
        self.prefix = prefix

    def build_key(self, infix, suffix):
        return ':'.join((self.prefix, infix, suffix))

    def inc(self, infix, suffix, execute_right_now=True):
        """将 self.prefix:infix:suffix 的值加1"""
        self.pipe.incr(self.build_key(infix, suffix))
        if execute_right_now:
            self.execute()

    def inc_n(self, infix, suffix, n=1, execute_right_now=True):
        """将 self.prefix:infix:suffix 的值加n"""
        self.pipe.incr(self.build_key(infix, suffix), n)
        if execute_right_now:
            self.execute()

    def set_val(self, infix, suffix, val, execute_right_now=True):
        """将 self.prefix:infix:suffix 的值设置为val"""
        self.pipe.set(self.build_key(infix, suffix), val)
        if execute_right_now:
            self.execute()

    def execute(self):
        return self.pipe.execute()


class ActorCounter(Counter):
    """对某日新增的Actor进行计数"""
    def __init__(self):
        super(ActorCounter, self).__init__()

    def count(self, actor, execute_right_now=True):
        # 中缀为 name@countryName
        infix = '@'.join((actor['location']['name'], actor['location']['countryName']))

        lat = actor['location']['lat']
        lng = actor['location']['lng']

        self.inc(infix, 'count', execute_right_now)
        self.set_val(infix, 'lat', lat, execute_right_now)
        self.set_val(infix, 'lng', lng, execute_right_now)

    @decorator._log('Count new actor...', 'Finished.')
    def count_actor_list(self, actor_list):
        for actor in actor_list:
            self.count(actor, execute_right_now=False)
        self.execute()

