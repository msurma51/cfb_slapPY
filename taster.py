import urllib.request
from bs4 import BeautifulSoup
from namespace_og import *
import re

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 

def pot(headers, url):
    request = urllib.request.Request(url,None,headers) #The assembled request
    response = urllib.request.urlopen(request)
    html = response.read().decode() # The data u need
    return(BeautifulSoup(html, "html.parser"))

url = input('Enter - ')
if len(url) < 1:
    url = 'https://godiplomats.com/sports/m-footbl/2021-22/boxscores/20210904_yzfh.xml'
soup = pot(headers,url)
url2 = url + '?view=plays'
soup2 = pot(headers,url2)

# Extract home and away names store in dict for ref
name_dict = dict()
team_names = soup.find_all('h4')
name_dict[away_name] = team_names[0].string
name_dict[home_name] = team_names[1].string

# Extract kicker names to determine name format for regex and opening kickoff
kick_headers = soup.find_all("th", string = 'Kickoffs')
kicker_names = list()
for header in kick_headers:
    k_names = list()
    k_table = header.parent.parent
    k_tags = k_table.find_all(class_ = 'nowrap')
    for tag in k_tags:
        for name in tag.stripped_strings:
            k_names.append(name)
    kicker_names.append(k_names)

name_dict[away_kicker] = kicker_names[0][0]
name_dict[home_kicker] = kicker_names[1][0]

#Extract play-by-play data from 'plays' view    
pbp = soup2.find_all(class_='stats-fullbox clearfix')[1]
rows = pbp.find_all('tr')
qtags = pbp.find_all(id = True)
dtags = pbp.find_all('th')

def dex_list(rows,tags):
    tag_dex = list()
    for i in range(len(rows)):
        if rows[i].contents[0] in tags:
            tag_dex.append(i)
    return(tag_dex)
    
qtag_dex = dex_list(rows,qtags)
qtag_dex.append(len(rows))
dtag_dex = dex_list(rows,dtags)
split_rows = [rows[qtag_dex[i]:qtag_dex[i+1]] for i in range(len(qtag_dex)-1)]
quarters = list()
for i in range(len(split_rows)):
    start_indices = [0] + [start - qtag_dex[i] for start in dtag_dex 
                     if start >= qtag_dex[i] and start < qtag_dex[i+1]]
    start_indices.append(len(split_rows[i]))
    drive_rows = [split_rows[i][start_indices[j]:start_indices[j+1]]
                  for j in range(len(start_indices)-1)]
    drive_strings = list()
    for drive in drive_rows:
        strings = list()
        for row in drive:
            seg = '\n' + ' '*6
            for string in row.stripped_strings:
                string = string.replace(seg,'')
                if 'back to top' not in string:
                    strings.append(string)
        drive_strings.append(strings)
    quarters.append(drive_strings)
    
# Extract home and away abbreviations from yard line string segments
abbr = list()
def abbr_finder(drive,abbr):
    for string in drive:
        yl_match = re.findall('([A-Z]+)[0-9]{2}',string)
        if len(yl_match)>0:
            for match in yl_match:
                abbr.append(match)
    return(abbr)
drive_count = 0
while len(set(abbr))<2:
    abbr = abbr_finder(quarters[0][drive_count],abbr)
    drive_count += 1
abbr2 = [name for name in abbr if name != abbr[0]][0]
name_dict[away_abbr] = None
# Determine whether home or away team kicked off, and match with first abbreviation
kicker_name = re.findall('([A-Za-z]+) kickoff',quarters[0][0][-1])
if len(kicker_name)>0:
    for kicker in kicker_names[0]:
        if kicker_name[0] in kicker:
            name_dict[away_abbr] = abbr[0]
            name_dict[home_abbr] = abbr2
            break
    if not name_dict[away_abbr]:        
        name_dict[home_abbr] = abbr[0]
        name_dict[away_abbr] = abbr2
    
            
# Point names to abbreviations
name_dict[name_dict[home_name]] = name_dict[home_abbr]
name_dict[name_dict[away_name]] = name_dict[away_abbr]


# As a test, print opening kickoff strings
def print_drive(drive):
    for string in drive:
        print(string)

print_drive(quarters[0][0])
