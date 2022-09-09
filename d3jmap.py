import json
import subprocess
import pandas as pd
import numpy as np

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]


df = pd.read_csv('d3jmap.csv', index_col='School')
new_match = df[(df['Match'].notnull()) & (df['Link'].isnull())].copy()
for index, row in new_match.iterrows():
    if row['Match'] in link_dict.keys():
        df.at[index,'Link'] = link_dict[row['Match']]

no_match = df[df['Match'].isnull()].index
key_list = [key for key in link_dict.keys() if key not in df['Match'].values]
key_list.sort()
key_match = list()

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
    
def jaccard(name,key):
    a = {char.upper() for char in name if char.isalpha()}
    b = {char.upper() for char in key if char.isalpha()}
    c = a & b
    d = a | b
    return len(c) / len(d)


pair_list = list()    
for team in no_match:
    for key in key_list:
        team_dict = dict()
        team_dict['School'] = team
        team_dict['Key'] = key
        team_dict['J'] = jaccard(team,key)
        pair_list.append(team_dict)
        
    
picc_df = pd.DataFrame(pair_list).sort_values('J', ascending = False)

while len(picc_df) > 0:
    row = picc_df.iloc[0]
    df.at[row['School'],'Match'] = row['Key']
    df.at[row['School'],'J'] = row['J']
    df.at[row['School'],'Link'] = link_dict[row['Key']]
    picc_df = picc_df[(picc_df['School'] != row['School']) & (picc_df['Key'] != row['Key'])]
df[['Match','J','Link']].to_csv('d3jmap.csv')
