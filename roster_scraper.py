from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl
import csv
import re
import sys

# Read in original roster
old_file = input('Enter old roster file:')
if len(old_file) < 1:
    old_file = '2021 Michigan Football Roster.csv'
with open(old_file, newline = '') as csvfile:
    reader = csv.DictReader(csvfile)
    old_roster = tuple(row for row in reader)
    
# Assign fieldnames to variables
jersey, first, last, height, weight, hometown, team, position, curr_class = reader.fieldnames

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Read in new roster link (ENTER returns current Michigan roster link)
url = input('Enter roster link:')
if len(url) < 1:
    url = 'https://mgoblue.com/sports/football/roster'
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

def pos_converter(roster_pos):
    conv_dict = {'RB':'HB', 'DE':'ED', 'DL':'DI'}
    rps = roster_pos.split('/')
    pff_pos = list()
    for i in range(len(rps)):
        if rps[i] in conv_dict.keys():
            pff_pos.append(conv_dict[rps[i]])
        else:
            pff_pos.append(rps[i])
    return ','.join(pff_pos)
    
def height_converter(roster_ht):
    feet_inches = re.findall('[0-9]+',roster_ht)
    if len(feet_inches[1]) > 1:
        return feet_inches[0] + feet_inches[1]
    else:
        return feet_inches[0] + '0' + feet_inches[1]
        
def number_converter(roster_number, pff_pos):
    off_pos = {'QB','HB','FB','WR','TE','OL','T','G','C'}
    def_pos = {'ED','DI','LB','DB','S','CB'}
    spt_pos = {'K','P','LS'}
    pos = pff_pos.split(',')[0]
    if pos in def_pos:
        return 'D' + roster_number
    elif pos in spt_pos:
        return 'S' + roster_number
    else:
        return roster_number
    
        
roster_states_us = ('Calif.', 'Colo.', 'Conn.', 'D.C.', 'Fla.', 'Ga.', 
                 'Hawaii', 'Idaho', 'Ill.', 'Kan.', 'La.', 'Mass.', 'Md.', 
                 'Mich.', 'Mo.', 'N.J.', 'N.Y.', 'Nev.', 'Ohio', 'Oregon', 
                 'Pa.', 'Tenn.', 'Texas', 'Va.', 'Wisc.')
state_abbrev_us = ('CA','CO','CT','DC','FL','GA','HI','ID','IL','KS','LA',
                'MA','MD','MI','MO','NJ','NY','NV','OH','OR','PA','TN',
                'TX','VA','WI')
state_map = {roster_states_us[i]: state_abbrev_us[i] for i in range(len(roster_states_us))}
    
    
def hometown_converter(roster_hometown,state_map):
    city_state = roster_hometown.split(', ')
    city = city_state[0]
    if city_state[1] in roster_states_us:   
        state = state_map[city_state[1]]
        return ", ".join((city,state,'US'))
    else:
        return ", ".join((city,city_state[1]))
        
        
def position_change(old_position, new_position):
    ol_pos = {'C','G','T'}
    db_pos = {'CB','S'}
    k_pos = {'K','P','K,P'}
    new_pos = new_position.split(',')[0]
    if old_position in ol_pos and new_pos == 'OL':
        return False
    elif old_position in db_pos and new_pos == 'DB':
        return False
    elif old_position in k_pos and new_pos in k_pos:
        return False
    elif old_position == new_pos:
        return False
    else:
        return True
             
# Initialize new roster list
new_roster = list()
# Find tag containing roster data
roster_tag = soup.find(class_= 'sidearm-roster-players')
# Isolate individual player data in iterable
players_raw = roster_tag('li')
# Some useful definitions for later
team_name = old_roster[0][team]
span_key = 'sidearm-roster-player-'
class_map = {'Fr.':'F', 'So.':'S', 'Jr.':'J', 'Sr.': 'SN', 'Gr.': 'G'}
# Extract, convert and compile relevant data for each player
for player in players_raw:
    player_dict = dict()
    # Name
    roster_name = player('h3')[0].a.string.split()
    player_dict[first] = roster_name[0]
    player_dict[last] = roster_name[1]
    # Position, height, weight
    pos_data = tuple(player(class_=span_key+'position')[0].stripped_strings)
    player_dict[position] = pos_converter(pos_data[0])
    player_dict[height] = height_converter(pos_data[1])
    player_dict[weight] = re.findall('^[0-9]{3}',pos_data[2])[0]
    # PFF Jersey Number
    roster_number = player('span', class_=span_key+'jersey-number')[0].string.strip()
    player_dict[jersey] = number_converter(roster_number, player_dict[position])
    # Hometown
    roster_hometown = player(class_=span_key+'hometown')[0].string
    player_dict[hometown] = hometown_converter(roster_hometown,state_map)
    # Current class year
    roster_class = player(class_=span_key+'academic-year')[0].string
    player_dict[curr_class] = class_map[roster_class]
    # Team
    player_dict[team] = team_name
    new_roster.append(player_dict)

# Create csv for new roster
new_file = '2022 %s Football Roster.csv' % team_name
with open(new_file, 'w', newline = '') as csvfile2:
    writer = csv.DictWriter(csvfile2, fieldnames = reader.fieldnames)
    writer.writeheader()
    writer.writerows(new_roster)

# Initialize change report document    
change_doc = '%s Update Doc.txt' % team_name
sys.stdout = open(change_doc, 'w')
# Initialize lists to separate departing from returning players
departing = list()
returning = list()
returning_new = list()
# Check all players in old roster for inclusion in new roster
for old_row in old_roster:
    same = [new_row for new_row in new_roster if old_row[last] == new_row[last] and old_row[first] == new_row[first]]
    #As an added measure, just in case...
    if len(same) > 1:
        same = [same_row for same_row in same if old_row[hometown] == same_row[hometown]]
    if len(same) < 1:
        departing.append(old_row)
    else:
        returning.append(old_row)
        returning_new.append(same[0])
returning_names = [(row[last],row[first]) for row in returning]
# Determine which players on the updated roster are new
incoming = [new_row for new_row in new_roster if (new_row[last],new_row[first]) not in returning_names]
# List departing and incoming players
print('The following players no longer play for %s:' % team_name)
for gone in departing:
    print(gone[jersey],gone[first],gone[last])
print('\nThe following players are new to %s:' % team_name)
for here in incoming:
    print(here[jersey],here[first],here[last])
# List changes for returning players
print('\nUpdate the following fields for returning players:')
update_string = '%s update field %s from %s to %s'
fields = (jersey, height, weight)
new_class_map = {'F':'S', 'S':'J', 'J':'SN', 'SN':'G', 'RSN':'G', 'G':'NULL'}
for j in range(len(returning)):
    full_name = returning[j][first] + ' ' + returning[j][last]
    if position_change(returning[j][position],returning_new[j][position]):
        print(update_string % (full_name, position, returning[j][position], returning_new[j][position]))
    for field in fields:
        if returning[j][field] != returning_new[j][field]:
            print(update_string % (full_name, field, returning[j][field], returning_new[j][field]))
    old_class = returning[j][curr_class]
    if new_class_map[old_class] != returning_new[j][curr_class]:
        print('%s %s do not update current class' % (returning[j][first], returning[j][last]))
                                                           
    
    
    
    
    



sys.stdout.close()
