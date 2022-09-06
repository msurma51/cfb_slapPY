import json
import pandas as pd

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]
link_archive = link_list[1]
link_dump = link_list[2]

df = pd.read_csv('d3jmap.csv', index_col='School')

df['Link'] = df['Match'].map(link_dict)
df.to_csv('d3jmap.csv')

with open('parsed_schedules.json', 'w') as outfile:
    json.dump([link_dict,link_archive,link_dump],outfile)