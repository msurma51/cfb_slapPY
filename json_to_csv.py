import json
import pandas as pd

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]
ser = pd.Series(link_dict).rename('Link').rename_axis('Key').sort_index()
df = pd.DataFrame(ser)
df.to_csv('link_dict.csv')

