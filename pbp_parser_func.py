from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from hudl_namespace import *
import ssl

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def pbp_parser(url):
    if len(url) < 1:
        url = 'https://lycomingathletics.com/sports/football/stats/2021/alvernia/boxscore/15038'
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser")

    # Extract home and away names and abbreviations, store in dict for ref
    name_dict = dict()
    drive_chart = soup.find(id='drive-chart')
    name_dict[home_name] = drive_chart('a', href='#home-drives')[0].string
    name_dict[away_name] = drive_chart('a', href='#visitor-drives')[0].string

    team_stats = soup.find(id="team-stats")
    name_dict[home_abbr] = team_stats('th',id='home-team')[0].string
    name_dict[away_abbr] = team_stats('th',id='away-team')[0].string
    
    # Point abbreviations to names
    name_dict[name_dict[home_abbr]] = name_dict[home_name]
    name_dict[name_dict[away_abbr]] = name_dict[away_name]
    
    # Extract game location, date and time
    name_dict[matchup] = '{} at {}'.format(name_dict[away_name],name_dict[home_name])
    info_tag = soup.find('dl', class_='text-center inline')
    dt = info_tag('dt')
    dd = info_tag('dd')
    info_dict = {dt[i].string:dd[i].string for i in range(len(dt))}
    name_dict[game_location] = info_dict['Site:']
    name_dict[game_date] = info_dict['Date:']
    name_dict[game_time] = info_dict['Kickoff Time:']

    # Extract kicker names to determine name format for regex and opening kickoff
    kickers = soup.find(id="individual-kickoffs-stats")
    header = kickers("th", scope = "row")
    kicker_names = list()
    for tag in header:
        name = list(tag.stripped_strings)[0]
        if name != 'Totals':
            kicker_names.append(name)

    name_dict[home_kicker] = kicker_names[-1]
    name_dict[away_kicker] = kicker_names[0]

    # Extract play-by-play data from box score link
    pbp = soup.find(id="play-by-play")
    quarters = list()
    for qtr in ('1st','2nd','3rd','4th','OT'):
        q_tags = pbp.find_all(id = qtr)
        # Create new list to store a list of strings for each drive
        drives = list()
        for q_tag in q_tags:      
            # Store each drive as a list of bs tags
            drives_raw = list(q_tag(['table', 'dl']))
            for drive in drives_raw:
                if drive.name == 'dl':
                    score_string = drive('dd')[0].string
                    drives[-1].append([score_string])
                else:
                    rows = drive('tr')
                    play_strings = list()
                    header_dex = 0
                    for row in rows:
                        strings = list()
                        header = row('th')
                        if all((len(header) > 0, header_dex == 0)) and header[0].string:
                            strings.append(header[0].string.strip())
                            header_dex = 1  
                        entries = row('td')
                        for entry in entries:
                            if entry.string:
                                string = entry.string.strip()
                                strings.append(string)
                            else:
                                string = ''
                                for hidden_string in entry.stripped_strings:
                                    string = '{} {}'.format(string,hidden_string)
                                if len(string) > 0:
                                    strings.append(string)
                        if len(strings) > 0:
                            play_strings.append(strings)
                    drives.append(play_strings)
        quarters.append(drives)
        
    # As a test, print opening kickoff strings
    def print_drive(drive):
        for string in drive:
            print(string)

    print_drive(quarters[0][0])
    return quarters, name_dict