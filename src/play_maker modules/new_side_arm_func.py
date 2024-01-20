from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from hudl_namespace import *
import ssl

# using firefox as the selenium browswer
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options

# used for searching elements by various structures
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

# suppressing the pop up window of what is happening
opts = Options()
opts.add_argument('--headless')
driver = Firefox(options=opts)

# regular expression
import re

def nsa_parse(url):
    if len(url) <1:
        url = 'https://mgoblue.com/sports/football/stats/2023/bowling-green/boxscore/25649'

    driver.get(url)
    time.sleep(5)
    num = 1

    # looking for the headers of the play by plays
    ## Box Score
    ## Team
    ## Individual
    ## Drive Chart
    ### Away Team
    ### Home Team
    ## Play-by-Play
    ### 1st
    ### 2nd
    ### 3rd
    ### 4th
    ### OT
    ## Participation
    all_buttons = driver.find_elements(By.TAG_NAME, 'button')

    # creating a list of all the buttons on inital load of page
    x=[]
    for i in all_buttons:
        x.append(i.text)

    # teams playing game
    team_names = []

    # clicking all buttons to load the correct pages
    for box_score in all_buttons:
        if box_score.text in ['Box Score','Team','Individual','Drive Chart','Play-By-Play','Participation']:
            print(box_score.text)
            box_score.click()
            time.sleep(7)
            # loading all the quarters of the game for Soup
            if box_score.text in ['Play-By-Play']:
                quarters = driver.find_elements(By.TAG_NAME, 'button')
                for qtr in quarters:
                    if qtr.text in ['1st','2nd','3rd','4th','OT']:
                        print(qtr.text)
                        qtr.click()
                        time.sleep(5)
            # getting the team names
            elif box_score.text in ['Drive Chart']:
                teams = driver.find_elements(By.TAG_NAME, 'button')
                for ii in teams:
                    if ii.text not in x + ['All']:
                        print(ii.text)
                        team_names.append(ii.text)
    
    # adding team names to dictionary
    name_dict = dict()
    name_dict[away_name] = team_names[0]
    name_dict[home_name] = team_names[1]

    # selenium to bs4
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'lxml')

    # closing out selenium
    driver.close()
    driver.quit()

    # team abbreviations
    name_dict[home_abbr] = str(soup.find(id="home-team").string).strip()
    name_dict[away_abbr] = str(soup.find(id="away-team").string).strip()
    # print(name_dict)

    # Point abbreviations to names
    name_dict[name_dict[home_abbr]] = name_dict[home_name]
    name_dict[name_dict[away_abbr]] = name_dict[away_name]
    # print(name_dict)

    # Extract game location, date and time
    name_dict[matchup] = '{} at {}'.format(name_dict[away_name],name_dict[home_name])

    info_tag = soup.find('dl', class_='text-center inline')
    dt = info_tag('dt')
    dd = info_tag('dd')
    info_dict = {str(dt[i].string).strip():str(dd[i].string).strip() for i in range(len(dt))}
    # print(info_dict)
    name_dict[game_location] = info_dict['Site:']
    name_dict[game_date] = info_dict['Date:']
    name_dict[game_time] = info_dict['Kickoff Time:']

    # Extract kicker names to determine name format for regex and opening kickoff
    kickers = soup.find(id="individual-kickoffs-stats")
    # print(kickers.prettify())
    header = kickers("td", {"class":"s-text-small","data-label":""})
    # print(header)
    kicker_names = list()
    for tag in header:
        name = list(tag.stripped_strings)[0]
        if name != 'Totals':
            kicker_names.append(name)

    name_dict[home_kicker] = kicker_names[-1]
    name_dict[away_kicker] = kicker_names[0]

    # Extract play-by-play data from box score link
    # pbp = soup.find(id="play-by-play")
    # need multiple pbp for each quarter/period
    quarters = list()
    for qtr in ('1st','2nd','3rd','4th','OT'):
        print(qtr)
        q_tags = soup.find_all(id = qtr)
        # print(q_tags)
        # Create new list to store a list of strings for each drive
        drives = list()
        for q_tag in q_tags:      
            # Store each drive as a list of bs tags
            drives_raw = list(q_tag(['table', 'dl']))
            for drive in drives_raw:
                if drive.name == 'dl':
                    score_string = drive('dd')[0].string.strip()
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
