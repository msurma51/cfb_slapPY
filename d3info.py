import urllib.request
from bs4 import BeautifulSoup
from hudl_namespace import *
from presto_prep import headers, pot
import pandas as pd

url = 'https://d3football.com/teams/index'
soup = pot(headers,url)
cup = soup(class_='teaminfo')[0]

team_list = list()
key_tags = cup('th')
keys = [tag.string for tag in key_tags]
team_tags = cup('tr')
for team_tag in team_tags[1:]:
    team_dict = dict()
    val = [string for string in team_tag.stripped_strings]
    for i in range(len(keys)):
        team_dict[keys[i]] = val[i]
    team_list.append(team_dict)
df = pd.DataFrame(team_list).rename_axis('Index')
df.to_csv('d3info.csv')
