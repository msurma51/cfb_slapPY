# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 15:46:33 2023

@author: surma
"""
import pandas as pd
import numpy as np
from presto_prep import headers, pot, presto_parser
from play_maker_funcs import name_extract
from bs4 import SoupStrainer


pd.set_option('display.max_columns', None)
url = 'https://lycomingathletics.com/sports/football/stats/2021/susquehanna/boxscore/15029'
#url = 'https://muhlenbergsports.com/sports/football/stats/2022/lebanon-valley/boxscore/4834'
#url = 'https://www.godiplomats.com/sports/m-footbl/2021-22/boxscores/20210911_9fo4.xml?view=plays'
# BS object of just the play-by-play
soup = pot(headers, url, strainer = SoupStrainer(id='play-by-play'))
if len(soup) > 0:
    # Pull a BS object for each quarter of the game
    quarter_sections = soup.find_all('section')[1:]
    # Initialize master df into which individual drive dataframes will be concatenated
    df = pd.DataFrame()
    for section in quarter_sections:
        html = str(section)
        drives = pd.read_html(html)
        # Ensure that each drive df has 2 columns, and mark the beginning of each quarter and drive
        for i in range(len(drives)):
            drive = drives[i]
            if len(drive.columns) == 1:
                drive.columns = ['play_str']
                drive['dd_str'] = ''
            else:
                drive.columns = ['dd_str', 'play_str']
            drive['qtr_first_row'] = False
            if i == 0:
                drive.at[0,'qtr_first_row'] = True
            drive['drive_first_row'] = drive.index == 0
        df = pd.concat((df,*drives))
        df.reset_index(drop = True, inplace = True)
else:
    df = presto_parser(url)

df.fillna('', inplace = True)
# Clean strings by eliminating multiple spaces between words
df['dd_str'] = df['dd_str'].str.split().str.join(sep = ' ')
# Extract down, distance and yard line from d&d string
dd_pattern = "(?P<down>[1-4])[dhnrst]{2} and (?P<dist>\d{1,2}|GOAL) at (?P<terr>[A-Z\d']+)(?P<yl_raw>[0-9]{2})"
df_ddyl = df['dd_str'].str.extract(dd_pattern)
df = pd.concat((df,df_ddyl), axis=1)

# Build name matching regex
fname_pat = "(?P<first>[A-Z][\w'-]+[.]?)"
lname_pat = "(?P<last>[A-Z][\w'-]+,?(?: Jr.)?(?: I{:3}V?)?)"
name_pat1 = "{} ?{}".format(fname_pat, lname_pat)
name_pat2 = "{}, ?{}".format(lname_pat, fname_pat)
name_patterns = [name_pat1,name_pat2]

# Extract run play info
# Get rusher and direction info using multiple possible patterns for both
direction_pat1 = " left| middle| right"
direction_pat2 = " over left end| up middle| over right end"
rush_dir_pat = "(?P<run_dir1>{})?".format(direction_pat1) + " rush" + "(?P<run_dir2>{})?".format(direction_pat2) 
# "Overlay" dataframes using concatenation and add columns to df
df_rusher = name_extract(df,"^",rush_dir_pat,*name_patterns, prefix = 'rusher_')
# Get gain/loss and yardline rushed to info
rush_pat2 = " rush" + "(?:{})?".format(direction_pat2)
run_gl_pat = " for (?P<run_gain>(?:loss of )?\d{1,2}) yards?"
run_ng_pat = " for (?P<run_gain>no gain)"
run_to_pat = " to the (?P<run_to_terr>[A-Z\d']+?)(?P<run_to_yl>[0-9]{1,2})"
# Create separate outputs for clear gains/losses and no gains, then overlay the latter into the former
df_gains = df['play_str'].str.extract(rush_pat2 + run_gl_pat + run_to_pat).fillna('')
df_noGain = df['play_str'].str.extract(rush_pat2 + run_ng_pat + run_to_pat).fillna('')
for col in df_gains.columns:
    df_gains[col] = df_gains[col] + df_noGain[col]
# Combine with main dataframe
df = pd.concat((df,df_rusher,df_gains),axis = 1)

# Extract pass play info
# Get passer, direction and result for passes thrown
pass_dir_pat = "(?P<pass_dir> LE| middle| RE)? pass (?P<pass_result>(?:in)?complete)"
df_passer = name_extract(df,"^",pass_dir_pat,*name_patterns, prefix = 'passer_')
# Get passer and result for sacks
df_sacked = name_extract(df,"^"," (?P<pass_result>sack)ed",*name_patterns, prefix = 'passer_')
# Overlay df_sacked into df_passer
for col in df_sacked.columns:
    df_passer[col] = df_passer[col] + df_sacked[col]
# Get intended receiver info
df_intended = name_extract(df," pass (?:in)?complete to ",'',*name_patterns, prefix = 'intended_')
# If pass is intercepted, get interceptor info
int_start_pat = " pass (?P<pass_result>intercepted) by "
int_end_pat = " at the (?P<int_terr>[A-Z\d']+?)(?P<int_yl>[0-9]{1,2})"
df_intercepted = name_extract(df,int_start_pat,int_end_pat,*name_patterns, prefix = 'intBy')
# Overlay inteception result into df_passer and drop column from df_intercepted
df_passer['pass_result'] = df_passer['pass_result'] + df_intercepted['pass_result']
df_intercepted.drop('pass_result', axis=1, inplace=True)
# Get player info for hurries and pass break-ups
df_brokenUpBy = name_extract(df,' broken up by','',*name_patterns,prefix = 'pbuBy')
df_hurriedBy = name_extract(df,' QB hurried by','',*name_patterns,prefix = 'hurriedBy')
pass_pats = [pattern.replace('run_','pass_') for pattern in (run_gl_pat, run_ng_pat, run_to_pat)]





