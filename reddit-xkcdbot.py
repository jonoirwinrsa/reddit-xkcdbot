#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Reddit xkcd Bot.

Posts useful comments on xkcd submissions in /r/xkcd

Requirements: feedparser, lxml
(install with pip: "pip install feedparser lxml")
'''

# By Tristan Harward, http://www.trisweb.com
# License: The MIT/X11 license (see LICENSE.md)

import sys
from sys import stdout, stdin
from time import sleep
import reddit
import os.path
import re
from time import strftime
from random import choice
import logging
import urllib2
import feedparser
from lxml import html
from lxml.cssselect import CSSSelector

reload(sys)
sys.setdefaultencoding("utf-8")

# Only argument supported so far is --debug, for running without making real submissions or changes.
if len(sys.argv) > 1 and sys.argv[1] == "--debug":
  debug = True
else:
  debug = False

if debug:
  logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s: %(message)s')
else:
  logging.basicConfig(filename='xkcdbot.log', level=logging.DEBUG, format='%(asctime)s: %(message)s')

logging.info("---\n--- Starting reddit-xkcdbot ---")

### Configuration! You can change these if you want.

VERSION = '2012-05-09'
APP_TITLE = 'reddit-xkcdbot'
USER_AGENT = APP_TITLE + '/' + VERSION + ' by /u/calinet6'

XKCD_RSS_URL = "http://xkcd.com/rss.xml"

# Reddit Username
USERNAME = "xkcd_bot"
# Place the password for the above user in this file all by itself. Don't make it public.
PASSWORD_FILENAME = "reddit-password.txt"
# Stores funny fortune strings, one per line with no quotes. Selects a random one for each comment. 
# You can add to this file and it will be re-read each time it's used, so no need to restart the bot or anything.
FORTUNE_FILENAME = "reddit-xkcdbot-fortunes.txt"
# Stores saved (already processed) xkcd posts by URL
SAVED_FILENAME = "reddit-xkcdbot-saved.txt"


### Functions!

'''Return a fun random string fortune!'''
def get_fun_string():
  try:
    fortune_file = open(FORTUNE_FILENAME, "r")
    fortune = choice(fortune_file.read().split("\n")).strip()
    fortune_file.close()
    return fortune
  except:
    pass
  return ""

'''Get the title text (hover tooltip text) of the given xkcd comic'''
def get_title_text(xkcd_number):
  try:
    feed = feedparser.parse(XKCD_RSS_URL)
    for item in feed["items"]:
      item_number = re.match("http:\/\/(www\.)?xkcd.(com|org)\/([0-9]+)\/?", item["link"]).group(3)
      if item_number == str(xkcd_number):
        # Found! Get the description and parse the "title" attribute.
        doc = html.fragment_fromstring(item["description"])
        return str(doc.attrib["title"])
  except Exception as e:
    print "Error encountered: {0}".format(e)
  return "(Not found)"

### Setup!

passf = open(PASSWORD_FILENAME, "r")
PASSWORD = passf.read().strip()
passf.close()

submitted = []
if os.path.isfile(SAVED_FILENAME):
  submitted_file = open(SAVED_FILENAME, 'r')
  submitted = submitted_file.read().split('\n')
  submitted_file.close()
else:
  submitted_file = open(SAVED_FILENAME, 'w')
  submitted_file.close()

# Poll every 5 minutes.
POLL_FREQUENCY = 300

### Main Loop!

try:
  while True:
    try:
      logging.info("Checking /r/xkcd for new submissions...")
      r = reddit.Reddit(user_agent=USER_AGENT)
      r.login(USERNAME, PASSWORD)
      submissions = r.get_subreddit('xkcd').get_new_by_date(limit=10)
      for s in submissions:
        if s.domain == "xkcd.com" and re.match("http:\/\/(www\.)?xkcd.(com|org)\/([0-9]+)\/?", s.url):
          if s.url not in submitted:
            logging.info("New xkcd submission found! {0} - {1}".format(s.title, s.url))
            existing_comment_found = False
            if not debug:
              for c in s.comments:
                if re.search("mobile version", c.body, re.IGNORECASE) or c.author == USERNAME:
                  existing_comment_found = True

            if not existing_comment_found:
              xkcd_number = re.match("http:\/\/(www\.)?xkcd.(com|org)\/([0-9]+)\/?", s.url).group(3)
              mobile_url = "http://m.xkcd.com/{0}/".format(xkcd_number)
              random_string = get_fun_string()
              title_text = get_title_text(xkcd_number)
              new_comment = "**[Mobile Version!]({0})**\n\n**Title text:** *{1}*\n\n    (Love, the new xkcd_bot. {2})".format(mobile_url, title_text, random_string)
              logging.info("  -> Adding Comment!: {0}".format(new_comment))
              retries = 0
              while True:
                try:
                  retries += 1
                  if not debug:
                    s.add_comment(new_comment)
                except reddit.errors.RateLimitExceeded as err:
                  if retries < 15:
                    logging.info("  {0} - Trying again in 60 seconds...".format(err.message))
                    sleep(60)
                    continue
                break
            # Save it!
            if not debug:
              submitted.append(s.url)
              submitted_file = open(SAVED_FILENAME, 'a')
              submitted_file.write("%s\n" % s.url)
              submitted_file.close()
    except urllib2.HTTPError as e:
      logging.info("ERROR: HTTPError code {0} encountered while making request - sleeping another iteration and retrying.".format(e.code))
    except urllib2.URLError as e:
      logging.info("URLError: {0} - sleeping another iteration and retrying.".format(e.reason))
    sleep(POLL_FREQUENCY)
except (KeyboardInterrupt):
  logging.info('Closing %s.' % APP_TITLE)
  quit()
