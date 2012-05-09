#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Reddit xkcd Bot.

Posts useful comments on xkcd submissions in /r/xkcd'''

from sys import stdout, stdin
from time import sleep
import reddit
import os.path
import re

# By Tristan Harward, http://www.trisweb.com
# License: The MIT/X11 license (see LICENSE.md)

VERSION = '2012-05-09'
APP_TITLE = 'reddit-xkcdbot'
USER_AGENT = APP_TITLE + '/' + VERSION + ' by /u/calinet6'

USERNAME = "xkcd_bot"
PASSWORD = "California1868"

SAVE_FILE = "reddit-xkcdbot-saved.txt"
submitted = []
if os.path.isfile(SAVE_FILE):
  submitted_file = open(SAVE_FILE, 'r')
  submitted = submitted_file.read().split('\n')
  submitted_file.close()
else:
  submitted_file = open(SAVE_FILE, 'w')
  submitted_file.close()

POLL_FREQUENCY = 60

try:
  while True:
    print "Checking /r/xkcd for new submissions..."
    r = reddit.Reddit(user_agent=USER_AGENT)
    r.login(USERNAME, PASSWORD)
    submissions = r.get_subreddit('xkcd').get_new_by_date(limit=10)
    for s in submissions:
      if s.domain == "xkcd.com" and re.match("http:\/\/(www\.)?xkcd.com\/([0-9]+)\/?", s.url):
        if s.ups > 10 and s.url not in submitted:
          print "xkcd submission found! {0} - {1}".format(s.title, s.url)
          existing_comment_found = False
          for c in s.comments:
            if re.search("mobile version", c.body, re.IGNORECASE) or c.author == USERNAME:
              print "  - Found bot or mobile version comment already! '{0}'".format(c.body)
              existing_comment_found = True
          if not existing_comment_found:
            xkcd_number = re.match("http:\/\/(www\.)?xkcd.com\/([0-9]+)\/?", s.url).group(2)
            mobile_url = "http://m.xkcd.com/{0}/".format(xkcd_number)
            new_comment = "[Mobile Version!]({0})".format(mobile_url)
            print "=== Adding Comment!: {0}".format(new_comment)
            #s.add_comment(new_comment)
          # save it!
          submitted.append(s.url)
          submitted_file = open(SAVE_FILE, 'a')
          submitted_file.write("%s\n" % s.url)
          submitted_file.close()
    sleep(POLL_FREQUENCY)
except (KeyboardInterrupt):
  print('Closing %s.' % APP_TITLE)
  quit()