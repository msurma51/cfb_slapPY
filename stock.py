from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer
import sys
import os
import ssl
import re
import subprocess

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

schedule_link = input('Enter schedule link -')
names_list = list()

proc = subprocess.run(['python','game_spider.py'], input=schedule_link, capture_output=True, text=True)
if proc.returncode == 0:
    box_score_links = proc.stdout.split()[4:]
    only_drive_chart = SoupStrainer(id='drive-chart')
    for url in box_score_links[0:2]:
        html = urlopen(url, context=ctx).read()
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
        
match_prop = 0.0
for name in names_list[0]:
    chars1 = len(set(name) & set(names_list[1][0]))
    chars2 = len(set(name) & set(names_list[1][1]))
    curr_prop = max(chars1,chars2)/len(name)
    if curr_prop > match_prop:
        match_prop = curr_prop
        team_name = name
scout = input('Is this opponent scout? (Y/N)')    
if not os.path.exists(team_name):
    os.mkdir(team_name)
f = open(team_name + '\\output.txt', 'w')
for url in box_score_links:
    proc = subprocess.run(['python','sauce.py'], input='{}\n{}\n{}\n{}'.format(url,scout,team_name,team_name), 
           capture_output=True, text=True)
    f.write(proc.stdout)
    f.write(proc.stderr)
    if proc.returncode == 0:    
        print(url + ' link successfully parsed')
    else:
        print(url + ' parse unsuccessful')
f.close()      
with open(team_name + '\\report.txt', 'w') as g:
    f = open(team_name + '\\output.txt', 'r')
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
            
    
    
