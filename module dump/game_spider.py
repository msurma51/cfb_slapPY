# To run this, download the BeautifulSoup zip file
# http://www.py4e.com/code3/bs4.zip
# and unzip it in the same directory as this file

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import ssl
import re

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter schedule link - ')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/schedule/2021'
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urlopen(req, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

def has_box_link(href):
    return(href and re.compile('boxscore').search(href))

box_score_tags = soup('a', href=has_box_link)
box_score_links = list()
url_start = url[:re.search('(\.com|\.edu|\.net|\.org)',url).span()[1]]
for tag in box_score_tags:
    link = url_start + tag['href']
    if link not in box_score_links:
        box_score_links.append(link)
for link in box_score_links:
    print(link)
    



