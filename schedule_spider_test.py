from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import re
import subprocess
import json

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter schedule link - ')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/schedule/2021'
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

team_tags = soup(class_='sidearm-schedule-game-opponent-name')
'''
page_links = list()
for tag in team_tags:
    link_start = tag.a.get('href')
    if link_start not in page_links:
        page_links.append(link_start)

# Schedule url formats for Sidearm (1st) and Presto (last 2)
url_ends = ('/sports/football/schedule/2021','/sports/fball/2021-22/schedule','/sports/m-footbl/2021-22/schedule')
infile = open('parsed_schedules.json').read()
inlist = json.loads(infile)
link_dict = inlist[0]
link_dump = inlist[1]
for link_start in page_links:
    if link_start in link_dump:
        print(link_start,'is a bad link')
        continue
    proc = None
    skip_dump = False
    for url_end in url_ends:
        link = link_start + url_end
        if link in link_dict.values():
            skip_dump = True
            break
        proc = subprocess.run(['python','stock.py'], input='{}\n{}'.format(link,'n'), capture_output=True, text=True)
        if proc.returncode == 0:
            output_first_line = proc.stdout.splitlines()[0]
            team_name = re.findall('Parsing schedule for (.*)', output_first_line)[0]
            link_dict[team_name] = link
            print(link + ' schedule parsed successfully')
            break
    if proc and all((proc.returncode == 1, not skip_dump)):
        link_dump.append(link_start)
        print(link_start + ' schedule parse unsuccessful')

with open('parsed_schedules.json', 'w') as outfile:
    json.dump([link_dict,link_dump],outfile)
    
'''