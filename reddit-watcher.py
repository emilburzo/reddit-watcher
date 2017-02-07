#!/usr/bin/env python

import requests
import requests.auth
import smtplib
import time
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from tinydb import TinyDB, Query
import os.path

# db
DB_PATH = '/tmp/reddit-watcher.json'
DB_INIT = True

# json api
JSON_URL = 'https://oauth.reddit.com/r/graticule.json'
USER_AGENT = 'linux:reddit-watcher:v1.0 (by /u/eaglex)'

# email
EMAIL_SUBJECT = 'reddit watcher'
EMAIL_FROM = 'reddit-watcher@yourdomain'
EMAIL_TO = 'youremail@yourdomain'
EMAIL_HOST = '127.0.0.1'
EMAIL_TEMPLATE = """\
<html>
  <head></head>
  <body>
    <div>
        <pre>
            @CONTENT@
        </pre>
    </div>

    <hr>

    <div>@LINK@</div>
  </body>
</html>
"""

###############

def job_exists(id):
    Job = Query()

    return db.search(Job.id == id)

def persist(id):
    if not job_exists(id):
        db.insert({'id': id})

if os.path.exists(DB_PATH):
    DB_INIT = False


###############

db = TinyDB(DB_PATH)

headers = {
    'User-Agent': USER_AGENT
}

# get token
client_auth = requests.auth.HTTPBasicAuth('appid', 'appsecret')
post_data = {"grant_type": "password", "username": REDDIT_USER, "password": REDDIT_PASS}
response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
access_token = response.json()['access_token']

# get data
headers = {
    'User-Agent': USER_AGENT,
    'Authorization': 'bearer ' + access_token
}

json = requests.get(JSON_URL, headers=headers).json()

for post in json['data']['children']:    
    job = post['data']

    id = job['id']
    link = job['url']
    body = job['selftext']
    subject = job['title'] + ' - ' + job['author']

    html = EMAIL_TEMPLATE.replace('@CONTENT@', body).replace('@LINK@', link)

    # only send email if we not at our first runtime
    # and the post doesn't already exist in the db
    if not DB_INIT and not job_exists(id):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        part = MIMEText(html, 'html', _charset="UTF-8")
        msg.attach(part)
        s = smtplib.SMTP(EMAIL_HOST)
        s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        s.quit()

    persist(id)


