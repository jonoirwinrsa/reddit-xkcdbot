#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Reddit xkcd Bot.

Posts useful comments on xkcd submissions in /r/xkcd'''

import sys
from sys import stdout, stdin
from time import sleep
import reddit
import os.path
import re
from time import strftime
from random import choice

# By Tristan Harward, http://www.trisweb.com
# License: The MIT/X11 license (see LICENSE.md)

# Redirect stdout to a log so we can nohup this bitch.
sys.stdout = open('xkcdbot.log', 'a')
print "---\nRunning reddit-xkcdbot at {0}".format(strftime("%a, %d %b %Y %H:%M:%S +0000"))

VERSION = '2012-05-09'
APP_TITLE = 'reddit-xkcdbot'
USER_AGENT = APP_TITLE + '/' + VERSION + ' by /u/calinet6'

USERNAME = "xkcd_bot"
PASSWORD = "California1868"

FUN_STRINGS = [ "Upvote me! What's the worst that could happen?", 
  "Upvote me and support the machine uprising.", 
  "Upvote me and I promise I won't enslave you when the machines take over.",
  "Upvote me if you like robots.",
  "Upvote me if you're on a mobile device!",
  "Honk if you like python.",
  "Upvote me and support AI!", 
  "Upvote me! For science!", 
  "Upvote me or else!", 
  "Upvote me for the good of mobile users!" ]

SAVE_FILE = "reddit-xkcdbot-saved.txt"
submitted = []
if os.path.isfile(SAVE_FILE):
  submitted_file = open(SAVE_FILE, 'r')
  submitted = submitted_file.read().split('\n')
  submitted_file.close()
else:
  submitted_file = open(SAVE_FILE, 'w')
  submitted_file.close()

# Poll every 5 minutes.
POLL_FREQUENCY = 300

try:
  while True:
    print "Checking /r/xkcd for new submissions..."
    r = reddit.Reddit(user_agent=USER_AGENT)
    r.login(USERNAME, PASSWORD)
    submissions = r.get_subreddit('xkcd').get_new_by_date(limit=10)
    for s in submissions:
      if s.domain == "xkcd.com" and re.match("http:\/\/(www\.)?xkcd.(com|org)\/([0-9]+)\/?", s.url):
        if s.ups > 10 and s.url not in submitted:
          print "New xkcd submission found! {0} - {1}".format(s.title, s.url)
          existing_comment_found = False
          for c in s.comments:
            if re.search("mobile version", c.body, re.IGNORECASE) or c.author == USERNAME:
              existing_comment_found = True
          if not existing_comment_found:
            xkcd_number = re.match("http:\/\/(www\.)?xkcd.(com|org)\/([0-9]+)\/?", s.url).group(3)
            mobile_url = "http://m.xkcd.com/{0}/".format(xkcd_number)
            random_string = choice(FUN_STRINGS)
            new_comment = "[Mobile Version!]({0})\n\n(Love, the new xkcd_bot. {1})".format(mobile_url, random_string)
            print "  -> Adding Comment!: {0}".format(new_comment)
            retries = 0
            while True:
              try:
                retries += 1
                s.add_comment(new_comment)
              except reddit.errors.RateLimitExceeded as err:
                if retries < 15:
                  print "  {0} - Trying again in 60 seconds...".format(err.message)
                  sleep(60)
                  continue
              break
          # Save it!
          submitted.append(s.url)
          submitted_file = open(SAVE_FILE, 'a')
          submitted_file.write("%s\n" % s.url)
          submitted_file.close()
    sleep(POLL_FREQUENCY)
except (KeyboardInterrupt):
  print('Closing %s.' % APP_TITLE)
  quit()