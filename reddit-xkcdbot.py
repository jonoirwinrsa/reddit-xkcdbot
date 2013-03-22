#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''Reddit xkcd Bot.

Posts useful comments on xkcd submissions in /r/xkcd

Requirements: praw
(install with pip: "pip install praw")
'''

# By Tristan Harward, http://www.trisweb.com
# License: The MIT/X11 license (see LICENSE.md)

import sys
from time import sleep
import praw
import os.path
import re
from random import choice
from random import randint
import logging
import urllib2
import json

reload(sys)
sys.setdefaultencoding("utf-8")

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

# Only argument supported so far is --debug, for running without making real submissions or changes.
if len(sys.argv) > 1 and sys.argv[1] == "--debug":
    debug = True
else:
    debug = False

if debug:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s: %(message)s')
else:
    logging.basicConfig(filename='xkcdbot.log', level=logging.INFO, format='%(asctime)s: %(message)s')

logging.info("---\n--- Starting reddit-xkcdbot ---")

### Configuration! You can change these if you want.

VERSION = '1.1'
APP_TITLE = 'reddit-xkcdbot'
USER_AGENT = APP_TITLE + '/' + VERSION + ' by /u/calinet6'
JSON_USER_AGENT = "python;{0}/{1}".format(APP_TITLE, VERSION)

URL_REGEX = "(https?:\/\/)?(www\.)?xkcd\.(com|org)\/([0-9]+).*"
ENABLE_TITLE_TEXT = True

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


def get_fun_string():
    '''Return a fun random string fortune!'''
    try:
        fortune_file = open(FORTUNE_FILENAME, "r")
        fortunes = fortune_file.read().strip().split("\n")
        fortune = choice(fortunes).strip()
        fortune_file.close()
        return fortune
    except:
        pass
    return ""


def get_json_data(xkcd_number):
    '''Get the title text (hover tooltip text) of the given xkcd comic'''
    try:
        json_url = "http://xkcd.com/{0}/info.0.json".format(xkcd_number)
        req = urllib2.Request(json_url, None, {'user-agent': JSON_USER_AGENT})
        json_data = json.load(urllib2.urlopen(req))
        return json_data
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
            r = praw.Reddit(user_agent=USER_AGENT)
            r.login(USERNAME, PASSWORD)
            submissions = r.get_subreddit('xkcd').get_new_by_date(limit=10)
            for s in submissions:
                matching = re.match(URL_REGEX, s.url, re.IGNORECASE)
                #logging.info("  (Checking {0} - {1}".format(s.title, s.url))
                if s.domain == "xkcd.com" and matching:
                    if (s.url not in submitted) and ("{0}{1}".format(s.url, s.id) not in submitted):
                        logging.info("New xkcd submission found! {0} - {1}".format(s.title, s.url))
                        existing_comment_found = False
                        if not debug:
                            for c in s.comments:
                                if re.search("mobile version", c.body, re.IGNORECASE) or c.author == USERNAME:
                                    existing_comment_found = True

                        if not existing_comment_found:
                            xkcd_number = re.match(URL_REGEX, s.url, re.IGNORECASE).group(4)
                            mobile_url = "http://m.xkcd.com/{0}/".format(xkcd_number)
                            random_string = get_fun_string()

                            version_text = "Mobile"
                            if randint(0, 100) > 95:
                                version_text = "Batmobile"

                            if ENABLE_TITLE_TEXT:
                                data = get_json_data(xkcd_number)
                                title_text = data["alt"]
                                img = data["img"]
                                title = data["title"]
                                random_thing_to_call_the_extra_text_to_fuck_with_people = choice(["Title text", "Title text", "Title text", "Alt text", "Hover text", "Subtext", "Extra junk", "Mouseover text", "Bat text"])
                                new_comment = "**[{0} Version!]({1})**\n\n[Direct image link: {4}]({5})\n\n**{2}:** {3}\n\n    ({6} Love, xkcd_bot.)".format(version_text, mobile_url, random_thing_to_call_the_extra_text_to_fuck_with_people, title_text, title, img, random_string)
                            else:
                                new_comment = "**[{0} Version!]({1})**".format(version_text, mobile_url)

                            logging.info("  -> Adding Comment!: {0}".format(new_comment))
                            retries = 0
                            while True:
                                try:
                                    retries += 1
                                    if not debug:
                                        s.add_comment(new_comment)
                                except praw.errors.RateLimitExceeded as err:
                                    if retries < 15:
                                        logging.info("  {0} - Trying again in 60 seconds...".format(err.message))
                                        sleep(60)
                                        continue
                                break
                        # Save it!
                        if not debug:
                            submitted.append("{0}{1}".format(s.url, s.id))
                            submitted_file = open(SAVED_FILENAME, 'a')
                            submitted_file.write("%s\n" % s.url)
                            submitted_file.close()
        except urllib2.HTTPError as e:
            logging.info("ERROR: HTTPError code {0} encountered while making request - sleeping another iteration and retrying.".format(e.code))
        except urllib2.URLError as e:
            logging.info("URLError: {0} - sleeping another iteration and retrying.".format(e.reason))
        except Exception as e:
            logging.info("Unknown error: " + str(e) + " sleeping another iteration and retrying.")
        sleep(POLL_FREQUENCY)
except (KeyboardInterrupt):
    logging.info('Closing %s.' % APP_TITLE)
    quit()
