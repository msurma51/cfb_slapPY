import json
import subprocess
import pandas as pd
import numpy as np

df_update = pd.read_csv('jmap_update.csv', index_col = 'School')
df_update = df_update.fillna('')

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]

for link in df_update['Link']:
    if len(link) > 0:
        proc = subprocess.run(['python','stock.py'], input='{}\n{}'.format(link,'n'), capture_output=True, text=True)
        if proc.returncode == 0:
            print(link + ' schedule parsed successfully')
        else:
            print(link + ' schedule parse unsuccessful')


'''
for link in df_update['Link']:
    if len(link) == 0:
        continue
    elif link in link_dict.values():
        print(link, 'parsed successfully')
    else:
        print(link, 'did not parse')
'''