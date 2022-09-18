import pandas as pd
import subprocess as sp
import re

team_df = pd.read_csv('d3info.csv', index_col='School')
week = input('Update to which week?')
week = int(week)
for index,row in team_df.iterrows():
    url = row['2022 Link']
    proc = sp.run(['python','rue.py'], input='{}\n{}\n{}\n{}'.format(url,index,'n',week), 
                  capture_output=True, text=True)
    if proc.returncode == 0:
        print(index,'update successful')
        print(proc.stdout.split('\n')[-2])
    else:
        print(index,'update failed')

with open('Schedules\\report.txt', 'w') as g:
    f = open('Schedules\\output.txt', 'r')
    write_set = {'\t', 'Exception', 'Score', 'Traceback', ' '}
    for line in f:
        for tag in write_set:
            if line.startswith(tag):
                g.write(line)
        if re.search('Error', line):
            g.write(line)
        for target in ('Player', 'Final'):
            dex = line.find(target)
            if dex > -1:
                g.write(line[dex:])
    f.close()    