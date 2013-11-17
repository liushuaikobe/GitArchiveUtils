# -*- coding: utf-8 -*-
'''
Created on 2013-11-17 13:34:32

@author: liushuai
@email: liushuaikobe@gmail.com
@last modified by: liushuai
@last modified on: 2013-11-17 13:34:32
'''
import config
import smtplib
from email.mime.text import MIMEText


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

