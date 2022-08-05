'''
from hudl_namespace import *
from pbp_parser_func import pbp_parser
from play_maker_hudl import game_builder
url = input('Enter - ')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/stats/2021/susquehanna/boxscore/15029'
quarters, name_dict = pbp_parser(url)
game_info = game_builder(quarters,name_dict)
game = game_info['game']
state = game_info['state']
#d0 = quarters[0][0]
#state.update(game_start)
#plays = drive_parser(d0,state,re_select,0,0)
'''
##urls = ['https://www.godiplomats.com/sports/m-footbl/2021-22/boxscores/20210904_yzfh.xml',
##        'https://lycomingathletics.com/sports/football/stats/2021/alvernia/boxscore/15038']

from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer
import ssl
import re
import subprocess

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

from game_spider import box_score_links
only_drive_chart = SoupStrainer(id='drive-chart')
'''
url = box_score_links[0]
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser", parse_only=only_drive_chart)
'''

names_list = list()
for url in box_score_links[0:2]:
    html = urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser", parse_only=only_drive_chart)
    names_list.append((soup.find('a', href='#home-drives').string, soup.find('a', href='#visitor-drives').string))
match_prop = 0.0
for name in names_list[0]:
    chars1 = len(set(name) & set(names_list[1][0]))
    chars2 = len(set(name) & set(names_list[1][1]))
    curr_prop = max(chars1,chars2)/len(name)
    if curr_prop > match_prop:
        match_prop = curr_prop
        team_name = name
scout = input('Is this opponent scout? (Y/N)')    
for url in box_score_links:
    try:
        proc = subprocess.run(['python','sauce.py'], input='{}\n{}\n{}'.format(url,scout,team_name), text=True)
        print(url + ' link successfully parsed')
    except:
        print(url + ' parse unsuccessful')
        print('error ' + str(IOError))