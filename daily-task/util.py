# -*- coding: utf-8 -*-
import config
import smtplib
from email.mime.text import MIMEText
import glob
import os


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





