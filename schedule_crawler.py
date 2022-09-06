import subprocess
import json

url = input('Enter schedule link -')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/schedule/2021'
used_links = list()
unused_links = [url,]
infile = open('parsed_schedules.json').read()
inlist = json.loads(infile)
link_dict = inlist[0]
while len(unused_links) > 0:
    url = unused_links[0]
    proc = subprocess.run(['python','schedule_spider.py'], input=url, capture_output=True, text=True)
    if proc.returncode == 0:
        print(url,'spidered successfully')
        infile = open('parsed_schedules.json').read()
        inlist = json.loads(infile)
        link_dict = inlist[0]
    else:
        print(url,'not spidered')
    used_links.append(url)
    unused_links = [link for link in link_dict.values() if link not in used_links]
    