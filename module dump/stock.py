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
try:
    only_drive_chart = SoupStrainer(id='drive-chart')
    for url in box_score_links[0:2]:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req, context=ctx).read()
        soup = BeautifulSoup(html, "html.parser", parse_only=only_drive_chart)
        names_list.append((soup.find('a', href='#home-drives').string, soup.find('a', href='#visitor-drives').string))
except:
    from presto_prep import headers, pot
    only_h4 = SoupStrainer('h4')
    for url in box_score_links[0:2]:
        soup = pot(headers, url, strainer = only_h4)
        names_list.append((soup('h4')[0].string,soup('h4')[1].string))
    
'''
if proc.returncode == 0:
    box_score_links = proc.stdout.split()[4:]
    only_drive_chart = SoupStrainer(id='drive-chart')
    for url in box_score_links[0:2]:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req, context=ctx).read()
        soup = BeautifulSoup(html, "html.parser", parse_only=only_drive_chart)
        names_list.append((soup.find('a', href='#home-drives').string, soup.find('a', href='#visitor-drives').string))
else:
    proc = subprocess.run(['python','game_spider_presto.py'], input=schedule_link, capture_output=True, text=True)
    box_score_links = proc.stdout.split()[4:]
    from presto_prep import headers, pot
    only_h4 = SoupStrainer('h4')
    for url in box_score_links[0:2]:
        soup = pot(headers, url, strainer = only_h4)
        names_list.append((soup('h4')[0].string,soup('h4')[1].string))
'''     
def jaccard(name,key):
    a = {char.upper() for char in name if char.isalpha()}
    b = {char.upper() for char in key if char.isalpha()}
    c = a & b
    d = a | b
    return len(c) / len(d)
    
pair_list = list()
j_score = 0
for name in names_list[0]:
    for name2 in names_list[1]:
        j_now = jaccard(name,name2)
        if j_now > j_score:
            team_name = name
            j_score = j_now

scout = input('Is this opponent scout? (Y/N)')
folder_path = 'Schedules\\' + team_name    
if not os.path.exists(folder_path):
    os.mkdir(folder_path)
f = open(folder_path + '\\output.txt', 'w')
infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]
print('Parsing schedule for ' + team_name)
for url in box_score_links:
    proc = subprocess.run(['python','sauce.py'], input='{}\n{}\n{}\n{}'.format(url,scout,team_name,team_name), 
           capture_output=True, text=True)
    f.write(proc.stdout)
    f.write(proc.stderr)
    if proc.returncode == 0:    
        link_dict[team_name] = schedule_link
        print(url + ' link successfully parsed')
    else:
        print(url + ' parse unsuccessful')
f.close()      
with open(folder_path + '\\report.txt', 'w') as g:
    f = open(folder_path + '\\output.txt', 'r')
    write_set = {'\t', 'Exception', 'Score', 'Traceback', ' '}
    for line in f:
        for tag in write_set:
            if line.startswith(tag):
                g.write(line)
        if re.search('Error', line):
            g.write(line)
        for target in ('Player', 'Final'):
            dex = line.find(target)
            if dex > -1:
                g.write(line[dex:])
with open('parsed_schedules.json','w') as outfile:
    json.dump([link_dict,*link_list[1:]],outfile)
    
    
