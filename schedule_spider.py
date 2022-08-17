from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import re
import subprocess

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter schedule link - ')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/schedule/2021'
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

team_tags = soup('span', class_='sidearm-schedule-game-opponent-name')
page_links = list()
for tag in team_tags:
    link_start = tag.a.get('href')
    if link_start not in page_links:
        page_links.append(link_start)

# Schedule url formats for Sidearm (1st) and Presto (last 2)
url_ends = ('/sports/football/schedule/2021','/sports/fball/2021-22/schedule','/sports/m-footbl/2021-22/schedule')
for link_start in page_links:
    for url_end in url_ends:
        link = link_start + url_end
        proc = subprocess.run(['python','stock.py'], input='{}\n{}'.format(link,'n'), text=True)
        if proc.returncode == 0:
            print(link + ' schedule parsed successfully')
            break
    if proc.returncode == 1:
        print(link_start + ' schedule parse unsuccessful')

   



