from urllib.request import urlopen
from bs4 import BeautifulSoup
from namespace_og import *
import ssl

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
if len(url) < 1:
    url = 'https://lycomingathletics.com/sports/football/stats/2021/alvernia/boxscore/15038'
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

# Extract home and away names and abbreviations, store in dict for ref
name_dict = dict()
drive_chart = soup.find(id='drive-chart')
name_dict[home_name] = drive_chart('a', href='#home-drives')[0].string
name_dict[away_name] = drive_chart('a', href='#visitor-drives')[0].string

team_stats = soup.find(id="team-stats")
name_dict[home_abbr] = team_stats('th',id='home-team')[0].string
name_dict[away_abbr] = team_stats('th',id='away-team')[0].string
# Point names to abbreviations
name_dict[name_dict[home_name]] = name_dict[home_abbr]
name_dict[name_dict[away_name]] = name_dict[away_abbr]

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
        drives_raw = list(q_tag("table"))
        for drive in drives_raw:
            strings = list()
            for string in drive.stripped_strings:
                strings.append(string)
            drives.append(strings)
    quarters.append(drives)
    

# As a test, print opening kickoff strings
def print_drive(drive):
    for string in drive:
        print(string)

print_drive(quarters[0][0])


