import urllib.request
from bs4 import BeautifulSoup
from presto_prep import headers, pot
import re


url = input('Enter schedule link - ')
if len(url) < 1:
    url = 'https://www.godiplomats.com/sports/m-footbl/2021-22/schedule'
soup = pot(headers,url)
def has_box_link(href):
    return(href and re.compile('boxscores').search(href))
box_score_tags = soup('a', class_='link', href=has_box_link)
box_score_links = list()
url_start = url[:re.search('\.com',url).span()[1]]

for tag in box_score_tags:
    link = url_start + tag['href']
    if link not in box_score_links:
        box_score_links.append(link)
for link in box_score_links:
    print(link)
