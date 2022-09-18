from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, SoupStrainer
import sys
import os
import ssl
import re
import subprocess
import json

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

schedule_link = input('Enter schedule link -')
names_list = list()

proc = subprocess.run(['python','game_spider_presto.py'], input=schedule_link, capture_output=True, text=True)
if proc.returncode == 1 or proc.stdout == 'Enter schedule link - ':
    proc = subprocess.run(['python','game_spider.py'], input=schedule_link, capture_output=True, text=True)
box_score_links = proc.stdout.split()[4:]

team_name = input('Who are you?')

scout = input('Is this opponent scout? (Y/N)')
folder_path = 'Schedules\\' + team_name    
if not os.path.exists(folder_path):
    os.mkdir(folder_path)

infile = open('parsed_games_2022.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]

week = input('Which week is it?')
f = open('Schedules\\output.txt', 'a')
print('Parsing games for ' + team_name)
for url in box_score_links[:int(week)]:
    if url not in link_dict.values():
        proc = subprocess.run(['python','sauce.py'], input='{}\n{}\n{}\n{}'.format(url,scout,team_name,team_name), 
               capture_output=True, text=True)
        f.write(proc.stdout)
        f.write(proc.stderr)
        if proc.returncode == 0:    
            print(url,'link successfully parsed')
        else:
            print(url,'parse unsuccessful')
f.close()
      

    
