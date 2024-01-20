import numpy as np
import pandas as pd

df_info = pd.read_csv('d3info.csv', index_col='School').drop('Index', axis=1)
df_jmap = pd.read_csv('d3jmap.csv', index_col='School')

df_join = df_info.join(df_jmap).drop('J', axis=1).rename(columns = {'Link':'2021 Link'})
df_join = df_join.fillna('')

def link_update(link):
    new_link = link.replace('-22','-23')
    new_link = new_link.replace('2021','2022')
    return new_link

df_join['2022 Link'] = df_join['2021 Link'].map(link_update, na_action='ignore')

df_join.to_csv('d3info.csv')
