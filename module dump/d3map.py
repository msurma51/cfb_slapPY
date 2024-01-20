import json
import pandas as pd

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]
key_list = [key for key in link_dict.keys()]
key_list.sort()

df = pd.read_csv('d3info.csv').sort_values('School')
key_match = list()
# First pass: direct matches
for team in df['School']:
    for key in key_list:
        match = None
        if team == key:
            match = key
            key_match.append(match)
            key_list.remove(match)
            break
    if not match:
        key_match.append(None)
df['Match'] = key_match

def find_match(row, key_list, criterion):
    if row['Match']:
        return(row['Match'])
    else:
        name = row['School']
        for key in key_list:
            if criterion(name,key):
                match = key
                key_list.remove(key)
                return(match)
        return(None)
    
def match1(name,key):
    a = {char for char in name if char.isalpha()}
    b = {char for char in key if char.isalpha()}
    c = a & b
    if all((name[:3] == key[:3], any((a == c, b == c)))):
        return True
    else:
        return False
        
for index,row in df.iterrows():
    df.at[index,'Match'] = find_match(row, key_list, match1)
    
df[['School','Match']].to_csv('d3map.csv')
name = 'Alfred State'
key = 'Alfred St.'