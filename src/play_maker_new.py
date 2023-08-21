# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 15:46:33 2023

@author: surma
"""
import pandas as pd
import numpy as np
import re
from presto_prep import headers, pot, presto_parser
from play_maker_funcs import name_extract, kick_extract, regex_check
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
df_rusher = name_extract(df['play_str'],"^",rush_dir_pat, name_patterns, prefix = 'rusher_')
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
df_passer = name_extract(df['play_str'],"^",pass_dir_pat,name_patterns, prefix = 'passer_')
# Get passer and result for sacks
df_sacked = name_extract(df['play_str'],"^"," (?P<pass_result>sack)ed", name_patterns, prefix = 'passer_')
# Overlay df_sacked into df_passer
for col in df_sacked.columns:
    df_passer[col] = df_passer[col] + df_sacked[col]
# Get intended receiver info
df_intended = name_extract(df['play_str']," pass (?:in)?complete to ",'', name_patterns, prefix = 'intended_')
# If pass is intercepted, get interceptor info
int_start_pat = " pass (?P<pass_result>intercepted) by "
int_end_pat = " at the (?P<int_terr>[A-Z\d']+?)(?P<int_yl>[0-9]{1,2})"
df_intercepted = name_extract(df['play_str'],int_start_pat,int_end_pat, name_patterns, prefix = 'intBy_')
# Overlay inteception result into df_passer and drop column from df_intercepted
df_passer['pass_result'] = df_passer['pass_result'] + df_intercepted['pass_result']
df_intercepted.drop('pass_result', axis=1, inplace=True)
# Get player info for hurries and pass break-ups
df_brokenUpBy = name_extract(df['play_str'],' broken up by','', name_patterns,prefix = 'pbuBy_')
df_hurriedBy = name_extract(df['play_str'],' QB hurried by','', name_patterns,prefix = 'hurriedBy_')
# Get gain/loss info for passes and sacks
pass_pats = [pattern.replace('run_','pass_') for pattern in (run_gl_pat, run_ng_pat, run_to_pat)]
pass_start_pat = " pass (?:in)?complete to.*?"
df_pass_gains = df['play_str'].str.extract(pass_start_pat + pass_pats[0] + pass_pats[2]).fillna('')
df_pass_noGain = df['play_str'].str.extract(pass_start_pat + pass_pats[1] + pass_pats[2]).fillna('')
df_sack_loss = df['play_str'].str.extract('sacked.*?' + pass_pats[0] + pass_pats[2]).fillna('')
for col in df_pass_gains.columns:
    df_pass_gains[col] = df_pass_gains[col] + df_pass_noGain[col] + df_sack_loss[col]
# Combine with main dataframe
df = pd.concat((df, df_passer, df_intended, df_intercepted, df_brokenUpBy, df_hurriedBy,
                df_pass_gains), axis = 1)

# Extract extra point info
df_xp = pd.DataFrame()
for xp_type in ('kick', 'rush', 'pass'):
    xp_result_pat = f' {xp_type} attempt (?P<xp_result>good|successful|no good|failed)'
    df_xp_type = name_extract(df['play_str'], '^', f' {xp_type} attempt', name_patterns, prefix = 'xp_')
    df_xp_type['xp_type'] = np.where(df_xp_type['xp_first'].str.len() > 0, xp_type, '')
    df_xp_result = df['play_str'].str.extract(xp_result_pat, flags = re.IGNORECASE).fillna('')
    df_xp_type['xp_result'] = df_xp_result['xp_result']
    if len(df_xp) == 0:    
        df_xp = pd.concat((df_xp, df_xp_type), axis = 1)
    else:
        for col in df_xp:
            df_xp[col] = df_xp[col] + df_xp_type[col]

fg_result_pat = ' field goal attempt from (?P<fg_dist>\d{1,2}) (?P<fg_result>good|successful|no good|failed)'
df_fg = name_extract(df['play_str'], '^', ' field goal attempt', name_patterns, prefix = 'fg_' )
df_fg = pd.concat((df_fg, df['play_str'].str.extract(fg_result_pat, flags = re.IGNORECASE)), axis = 1).fillna('')

# Extract kickoff and punt info
df_ko = kick_extract(df['play_str'], 'kickoff', name_patterns)
df_punt = kick_extract(df['play_str'], 'punt', name_patterns)
df_kp = df_ko + df_punt


# Extract return info
df_return = name_extract(df['play_str'], '', ' return', name_patterns, prefix = 'retBy_')
df_retYards = df['play_str'].str.extract("return (?P<ret_yards>\d{1,2}) yard(?:s)?")
yl_str = "return .*? to the (?P<ret_terr>[A-Z\d']+?)(?P<ret_yl>[0-9]{1,2})"
df_retYL = df['play_str'].str.extract(yl_str)
df_return = pd.concat((df_return, df_retYards, df_retYL), axis = 1)
df = pd.concat((df, df_xp, df_kp, df_fg, df_return), axis = 1)

# Extract tackler info
df['tackle_str'] = df['play_str'].str.extract('(.*)(?:PENALTY.*)$')
df['tackle_str'] = np.where(df['tackle_str'].isna(), df['play_str'], df['tackle_str'])
tackler_strings = df['tackle_str'].str.extract("\((.*)\)").squeeze().str.strip().fillna('')
tackler_df = tackler_strings.str.split(pat = ';', expand = True).fillna('')
df_tackler1 = name_extract(tackler_df[0], '', '', name_patterns, prefix = 'tackler1_')
df_tackler2 = name_extract(tackler_df[1], '', '', name_patterns, prefix = 'tackler2_')

# Extract penalty info
df['pen_str'] = df['play_str'].str.extract('(PENALTY.*)', flags = re.IGNORECASE)
df['presnap_pen'] = df['play_str'].str.startswith('PENALTY')
player_pen_strings = df['pen_str'].str.extract("\((.*)\)").squeeze().str.strip().fillna('')
df_pen = name_extract(player_pen_strings, '', '', name_patterns, prefix = 'penOn_')
pen_pat = "PENALTY (?P<pen_team>[A-Z'\d]+) (?P<penalty>[a-zA-Z ]+[a-zA-Z])? ?(?P<pen_yards>\d{1,2})"
df_pen = pd.concat((df_pen,df['pen_str'].str.extract(pen_pat)), axis = 1)


# Extract fumble info
df['fumble_str'] = df['play_str'].str.extract(' (fumble.*)')
df_fum = name_extract(df['fumble_str'], 'fumble by ', '', name_patterns, prefix = 'fumbleBy_')
recov_by_pat = "recovered by (?P<recovery_team>[A-Z\d']+) "
df_fum = pd.concat((df_fum, name_extract(df['fumble_str'], recov_by_pat, '', 
                                         name_patterns, prefix = 'recoveredBy_')), axis = 1)
fum_yl = df['fumble_str'].str.extract("at (?P<recov_terr>[A-Z\d']+?)(?P<recov_yl>[0-9]{1,2})")
df_fum = pd.concat((df_fum, fum_yl), axis =1)
df = pd.concat((df, df_tackler1, df_tackler2, df_fum, df_pen), axis = 1)

# Get times where posted
df['game_clock'] = ''
for token in (' at', ' clock'):
    time_series = df['play_str'].str.extract(token + ' (\d{1,2}:\d{2})').squeeze().fillna('')
    df['game_clock'] = df.game_clock + time_series
df['game_clock'] = df['game_clock'].replace('', np.NaN).ffill().bfill()

# Set boolean values for certain events
for tag in ['TOUCHDOWN', 'NO PLAY', 'Timeout']:
    colname = '_'.join(tag.lower().split())
    df[colname] = np.where(df['play_str'].str.contains(tag, flags = re.IGNORECASE), 1, 0)

regex_check(df['play_str'].str.contains('TOUCHDOWN'))

