# To run this, download the BeautifulSoup zip file
# http://www.py4e.com/code3/bs4.zip
# and unzip it in the same directory as this file

from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import re

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

box_score_tags = list(
    soup(attrs = {"class" : "sidearm-schedule-game-links-boxscore"}))
box_score_links = list()
url_start = url[:re.search('\.com',url).span()[1]]
for tag in box_score_tags:
    link = url_start + tag('a')[0].get('href',None)
    box_score_links.append(link)
for link in box_score_links:
    print(link)
    
    
    



