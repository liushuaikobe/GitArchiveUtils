# -*- coding: utf-8 -*-
import glob
import os
import csv

import smtplib
from email.mime.text import MIMEText
from whoosh import index
from whoosh.fields import Schema, TEXT

import config
from database import get_redis_pipeline


mail_config = config.mail_config

def sendmail(sbj, content, 
    fromwhom=mail_config['from'], towhom=mail_config['to'], 
    server=mail_config['server'], username=mail_config['username'], pwd=mail_config['pwd']):
    try:
        msg = msg.encode('utf-8')
    except Exception, e:
        pass
    msg = MIMEText(content)
    msg['Subject'] = sbj
    msg['From'] = fromwhom
    msg['To'] = towhom
    s = smtplib.SMTP(server)
    s.ehlo()
    s.starttls()
    s.login(username, pwd)
    s.sendmail(fromwhom, towhom, msg.as_string())


def detect(base, year, month, day):
    """检测指定base目录下的某天的文件是否齐全"""
    kwargs = {'year': year, 'month': month, 'day': day}
    f_name = '{year}-{month:02d}-{day:02d}-*.json.gz'.format(**kwargs)
    r1 = os.path.join(base, f_name)
    r2 = '*.json.gz'
    return len(glob.glob(r1)) == 24 and len(glob.glob(r2)) == 0


class WhooshUtil(object):
    """Whoosh搜索相关工具"""
    def __init__(self, ix_path=config.ix_path):
        super(WhooshUtil, self).__init__()
        self.ix_path = ix_path
        self.schema = Schema(location=TEXT(stored=True), rlocation=TEXT(stored=True))
        
    def build_whoosh_index(self):
        """建立location的Whoosh搜索索引"""
        if not os.path.exists(self.ix_path):
            os.mkdir(self.ix_path)
            ix = index.create_in(self.ix_path, self.schema)
        else:
            ix = index.open_dir(self.ix_path)
        self.writer = ix.writer()

    def add_search_doc(self, location, rlocation, execute_right_now=True):
        """添加搜索内容"""
        self.writer.add_document(location=unicode(location, 'utf-8'), rlocation=unicode(rlocation, 'utf-8'))
        if execute_right_now:
            self.writer.commit()

    def commit(self):
        self.writer.commit()
        

def grcount2csv(output_path=config.csv_path):
    """把grcount的信息转化成CSV文件，以便在前端展示"""

    with open(os.path.join(output_path, 'grcount.csv'), 'wb') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['title', 'country', 'count', 'latitude', 'longitude'])

        pipe = get_redis_pipeline()
        keys_pattern = ':'.join((config.redis_count_prefix, '*', 'lng'))
        pipe.keys(pattern=keys_pattern)
        keys = pipe.execute()
        for key in keys[0]:
            prefix, location_and_counttry, item = key.split(':')

            title, country = location_and_counttry.split('@')
        
            pipe.get(':'.join((prefix, location_and_counttry, 'lat')))
            pipe.get(':'.join((prefix, location_and_counttry, 'lng')))
            pipe.get(':'.join((prefix, location_and_counttry, 'count')))

            lat, lng, count = pipe.execute()

            csv_writer.writerow([title, country, count, lat, lng])

