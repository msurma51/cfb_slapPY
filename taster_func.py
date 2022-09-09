import urllib.request
from bs4 import BeautifulSoup
from hudl_namespace import *
from presto_prep import headers, pot
import re

def taster(url):
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
    
    # Extract game location, date and time
    setting_tag = soup.find(class_='align-center')
    setting_strings = [string for string in setting_tag.stripped_strings]
    name_dict[matchup] = setting_strings[0]
    city = re.findall('[A-Z].*',setting_strings[1])
    date = re.findall('\d+/\d+/\d+', setting_strings[2])
    time = re.findall('- (.*)', setting_strings[2])
    setting_dict = {game_location: city, game_date: date, game_time: time}
    for key in setting_dict.keys():
        if len(setting_dict[key]) > 0:
            name_dict[key] = setting_dict[key][0]
    
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
            elif len(rows[i].contents) > 1 and rows[i].contents[1] in tags:
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
            play_strings = list()
            for row in drive:
                strings = list()
                entries = row.find_all(['th','td'])
                seg = '\n' + ' '*6
                for entry in entries:
                    if entry.find('div'):
                        entry = entry.find_all('div')[0]
                    string = entry.string.replace(seg,'').strip()
                    string = string.replace('\n','')
                    strings.append(string)
                if 'back to top' not in strings:
                    play_strings.append(strings)
            drive_strings.append(play_strings)
        quarters.append(drive_strings)
       
    # Extract home and away abbreviations from yard line string segments
    abbr = list()
    def abbr_finder(drive,abbr):
        for play in drive:
            yl_match = re.findall("([A-Z&']+)[0-9]{2}",play[0])
            if len(yl_match)>0:
                for match in yl_match:
                    abbr.append(match)
        return(abbr)
    drive_count = 0
    while len(set(abbr))<2:
        abbr = abbr_finder(quarters[0][drive_count],abbr)
        drive_count += 1
    ko_string = quarters[0][0][-1][-1]
    kicker_name = re.findall('([A-Za-z]+) kickoff',ko_string)
    kicker = None
    if len(kicker_name)>0:
        if name_dict[away_kicker] in kicker_name[0]:
            kicker = name_dict[away_kicker]
        elif name_dict[home_kicker] in kicker_name[0]:
            kicker = name_dict[home_kicker]
        else:
            k = {char for char in kicker_name[0] if char.isalpha()}
            a = k & set(name_dict[home_kicker])
            b = k & set(name_dict[away_kicker])
            if k == a:
                kicker = name_dict[home_kicker]
            elif k == b:
                kicker = name_dict[away_kicker]    

    # Determine whether possession was determined in opening kick drive strings
    kick_team = None
    for row in quarters[0][0]:
        has_ball = re.findall('ball on ([A-Z]+)[0-9]{2}', row[-1])
        if len(has_ball) > 0:
            kick_team = has_ball[0]
            break

    name_dict[home_abbr] = None
    name_dict[away_abbr] = None

    # Match kicker with kick team abbr, assign remaining abbr to other team
    if kicker and kick_team in abbr:
        abbr2 = [name for name in abbr if name != kick_team][0]
        if kicker == name_dict[home_kicker]:
            name_dict[home_abbr] = kick_team
            name_dict[away_abbr] = abbr2
        else:
            name_dict[home_abbr] = abbr2
            name_dict[away_abbr] = kick_team

    # Determine abbr using kicker home or away and which territory he kicked the ball to
    if not name_dict[home_abbr] and kicker:
        yards = re.findall('kickoff (\d+) yards to the ([A-Za-z]+)[\d]{2}', ko_string)
        if len(yards) > 0:
            kick_yards = int(yards[0][0])
            kick_terr = yards[0][1]
            abbr2 = [name for name in abbr if name != kick_terr][0]
            if kick_yards > 14:
                if kicker == name_dict[away_kicker]:
                    name_dict[home_abbr] = kick_terr
                    name_dict[away_abbr] = abbr2
                else:
                    name_dict[away_abbr] = kick_terr
                    name_dict[home_abbr] = abbr2
            else:
                if kicker == name_dict[away_kicker]:
                    name_dict[away_abbr] = kick_terr
                    name_dict[home_abbr] = abbr2
                else:
                    name_dict[home_abbr] = kick_terr
                    name_dict[away_abbr] = abbr2
                    
    # If you could not identify the opening kicker or kick team, compare abbreviations to team names
    if not name_dict[home_abbr]:
        for curr_abbr in set(abbr):
            abbr2 = [name for name in abbr if name != curr_abbr][0]
            home_prop = len(set(curr_abbr) & set(name_dict[home_name].upper())) / len(set(curr_abbr))
            away_prop = len(set(curr_abbr) & set(name_dict[away_name].upper())) / len(set(curr_abbr))
            if home_prop == away_prop:
                continue
            elif home_prop > away_prop:
                name_dict[home_abbr] = curr_abbr
                name_dict[away_abbr] = abbr2
                break
            else:
                name_dict[away_abbr] = curr_abbr
                name_dict[home_abbr] = abbr2
                break
                
    if not name_dict[home_abbr]:
        print('Abbreviations could not be matched')

    # Point abbreviations to names
    name_dict[name_dict[home_abbr]] = name_dict[home_name]
    name_dict[name_dict[away_abbr]] = name_dict[away_name]


    # As a test, print opening kickoff strings
    def print_drive(drive):
        for string in drive:
            print(string)

    print_drive(quarters[0][0])
    return quarters, name_dict