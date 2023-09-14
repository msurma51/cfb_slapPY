# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 06:50:40 2023

@author: surma
"""

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import datetime
import re
from presto_prep import headers, pot, get_info_dict
from bs4 import SoupStrainer
from play_maker_base import play_maker
from play_maker_funcs import (name_patterns, possession, possession_final, points_on_play, kick_result, 
                              play_duration, clean_direction)


pd.set_option('display.max_columns', None)
#url = 'https://lycomingathletics.com/sports/football/stats/2021/susquehanna/boxscore/15029'
#url = 'https://muhlenbergsports.com/sports/football/stats/2022/franklin-marshall/boxscore/4600'
#url = 'https://godiplomats.com/sports/football/stats/2023/lebanon-valley-college/boxscore/12182'
#url = 'https://wvusports.com/sports/football/stats/2022/baylor/boxscore/18685' # def PAT
#url = 'https://muhlenbergsports.com/sports/football/stats/2022/lebanon-valley/boxscore/4834'
url = 'https://bryantbulldogs.com/sports/fball/2023-24/boxscores/20230909_f6un.xml'
# BS object of just the play-by-play
soup = pot(headers, url, strainer = SoupStrainer(id='play-by-play'))
presto = False
if len(soup) < 1:
    soup = pot(headers, url + '?view=plays', strainer = SoupStrainer(class_='stats-fullbox clearfix'))
    soup = soup.find_all('table')[1]
    presto = True
# fname = 'lyco_pbp.html'
# with open(fname, 'r') as infile:
#     html = infile.read()
# strainer = SoupStrainer(id='play-by-play')
# soup = BeautifulSoup(html, "html.parser", parse_only = strainer)
df = play_maker(soup, name_patterns, presto = presto)

# Identify R/P/K play types
df['play_type'] = np.where(df.play_str.str.contains(' rush'), 'Run', 
                           np.where(df.pass_result != '', 'Pass', 
                                    np.where(df.kick_type != '', df.kick_type.str.capitalize(), 
                                             np.where(df.fg_result != '', 'FG', ''))))
# Add kneels as type run
df['play_type'] = df.play_type.mask(df.kneel == 1, 'Run')
# Fill / overwrite with XP plays
df['play_type'] = np.where(df.xp_type == 'kick', 'Extra Pt.', 
                           np.where(df.xp_type.isin(['rush', 'pass']), '2 Pt.', df.play_type))
# Fill with timeouts, pre-snap penalties
df['play_type'] = df.play_type.mask(df.timeout == 1, 'Timeout')
df['play_type'] = df.play_type.mask(df.presnap_pen == True, 'Penalty')
# Identify attempt type (R/P) for 2 Pt. attempts
df['try_type'] = np.where(df.play_type == '2 Pt.', df.xp_type.str.capitalize(), '')
df['try_type'] = df.try_type.replace('Rush', 'Run')

# Clean DDYL
df['dist'] = np.where(df.dist.str.contains('GOAL'), df.yl_raw, df.dist)
df['terr'] = df.terr.fillna('')
# Convert integer strings to ints while preserving nans
for int_col in ('down', 'dist', 'yl_raw'):
    df[int_col] = np.where(df[int_col].isna(), df[int_col], df[int_col].fillna(0).astype('int64'))
# Combine run and pass gains for gain_loss column
df['gain_loss'] = ''
for gain in ['run_gain', 'pass_gain']:
    loss_key = gain[:gain.index('gain')] + 'loss'
    gl = pd.Series(np.where(df[loss_key] == 1, '-' + df[gain], 
                            np.where(df[gain].str.contains('no'), '0', df[gain])))
    df['gain_loss'] = df.gain_loss + gl
df['gain_loss'] = np.where(df.gain_loss == '', np.NaN, df.gain_loss.replace('',0).astype('int64'))
# Convert 'to_yl' and '_yards' to int/NA types as above   
df['gnls_to_yl'] = df.run_to_yl + df.pass_to_yl
df['gnls_to_terr'] = df.run_to_terr + df.pass_to_terr
ydyl_cols = [col for col in df.columns if re.search('_yl$', col) or re.search('_yards$', col)]
for col in ydyl_cols:
    try:
        df[col] = df[col].replace('',np.NaN)
        df[col] = np.where(df[col].isna(), df[col], df[col].fillna(0).astype('int64'))
    except Exception as e:
        print('Error for column name ', col)
        print(e)
        raise
        
# Merge run and pass directions into individual columns (respectively) and convert values to L/M/R
for col in ('run_dir', 'pass_dir'):
    df[col] = (df[col + '1'] + df[col + '2']).map(clean_direction)
    

    
# Add quarter and overall 'drive' counts
for first_row, colname in zip(('qtr_first_row', 'drive_first_row'),('quarter', 'drive_num')):
    ser = df.groupby(first_row).cumcount()
    ser = np.where(df[first_row] == False, np.NaN, ser)
    df[colname] = (ser+1)
    df[colname] = df[colname].ffill().astype('int64')
df['drive_count'] = df.groupby('drive_num').cumcount()

# Merge first and last names into full name for export
first_cols = [col for col in df.columns if re.search('_first$', col)]
last_cols = [col for col in df.columns if re.search('_last$', col)]
name_cols = [col[:col.index('_last')] for col in last_cols]
df_name = pd.DataFrame()
for i, colname in enumerate(name_cols):
    name_col = df[[first_cols[i], last_cols[i]]].apply(' '.join, axis = 1).rename(colname)
    name_col = name_col.str.strip().replace('TE AM', 'TEAM')
    df_name = pd.concat((df_name, name_col), axis = 1)
df_name['rusher'] = df_name.rusher.mask(df.try_type == 'Rush', df_name.xp)
df_name['rusher'] = df_name.rusher.mask(df.kneel == 1, 'TEAM')
df_name['passer'] = df_name.passer.mask(df.try_type == 'Pass', df_name.xp)
# Merge xp/fg kicker into kicker into 'kicker' name column
df_name['kicker'] = np.where(df.xp_type == 'kick', df_name.xp,
                             np.where(df.play_type == 'FG', df_name.fg, df_name.kicker))
df = pd.concat((df, df_name), axis = 1)

# Determine possession at the beginning of each play
teams = [team for team in df.terr.unique() if team != '']
df['poss'] = df.apply(possession, args = (teams,), axis = 1)
for role in ('passer', 'rusher', 'intended', 'kicker'):
    try:
        role_map = df[(df[role] != '') & (df['poss'] != '')][[role, 'poss']].drop_duplicates().set_index(role).squeeze()
        df['poss'] = df.poss.mask(df.poss == '', df[role].map(role_map)).fillna('')
    except Exception as e:
        print(role, e)
team_cat_ordered = CategoricalDtype(categories = sorted(teams + ['']), ordered = True)
df['poss'] = df.poss.astype(team_cat_ordered)
df['drive_poss'] = df.groupby('drive_num')['poss'].transform(max)
df['poss'] = np.where(df.drive_count == 0, df.drive_poss, df.poss.replace('', np.NaN))
df['poss'] = df.poss.ffill()

# Convert yl to +/- depending on possession and territory
df['yl'] = np.where((df.terr == df.poss) & (df.yl_raw != 50), df.yl_raw * -1, df.yl_raw)
#df['pen_yards'] = df.pen_yards.fillna(0).astype('int64')
for result_col in ('pass_result', 'fg_result', 'xp_type', 'xp_result', 'penalty'):
    df[result_col] = df[result_col].str.title().replace({'Successful': 'Good', 
                                                         'Failed': 'No Good', 
                                                         'Blocked': 'No Good'})
df['gain_loss'] = np.where(df.pass_result == 'Incomplete', 0, df.gain_loss)
    
# Fix PBUs captured as tackles
pbu = np.where((df.pass_result == 'Incomplete' ) & (df.tackler1 != ''), df.tackler1, '')
df['pbuBy'] = df.pbuBy + pbu
df['tackler1'] = np.where(pbu != '', '', df.tackler1)

# Add KO/Punt Result
recov_by_pat = "recovered by (?P<recovery_team>[A-Z\d']+) "
df['kick_result'] = df.apply(kick_result, axis = 1)

# Associate timeouts with the previous play
df['timeout'] = np.where(df.play_type == 'Timeout', 1, np.NaN)
df['timeout'] = df.timeout.shift(-1)

# Determine possession at the end of each play (not for the next play)
df['poss_final'] = df.apply(possession_final, args = (teams,), axis = 1)
    
# Create player map to be used in determining home and away team
players = df[['rusher', 'passer', 'kicker']].agg(sum, axis = 1).rename('player')
player_map = pd.concat((players, df.poss), axis = 1).drop_duplicates() 
player_map = player_map[(player_map.player != '') & (player_map.poss != '')].set_index('player').squeeze()
# Get game-level box score info
if presto:
    box_soup = pot(headers, url)
    rurl = url[:url.find('boxscores')] + 'roster'
    #roster_soup = 
else:
    box_soup = pot(headers, url, strainer = SoupStrainer(id='box-score'))
    rurl = url[:url.find('stats')] + 'roster'
    roster_soup = pot(headers, rurl)
info_dict = get_info_dict(box_soup, player_map, name_patterns, presto = presto)

# Add points scored on each play and cumulative team score
for prefix in ('away_', 'home_'):
    df[prefix + 'points_on_play'] = df.apply(points_on_play, args = (info_dict[prefix + 'abbr'],), axis = 1)
    df[prefix + 'points'] = df[prefix + 'points_on_play'].cumsum().shift(1).fillna(0)
    


view_cols = ['quarter', 'game_clock', 'drive_num', 'drive_count', 'poss', 
             'down', 'dist', 'yl', 'terr', 'play_type',
            'gain_loss', 'gnls_to_yl', 'gnls_to_terr', 'rusher', 'run_dir', 
            'passer', 'pass_dir', 'pass_depth', 'intended', 'pass_result', 
            'intBy', 'int_terr', 'int_yl', 'pbuBy', 'hurriedBy',
            'kicker', 'kick_yards', 'kick_terr', 'kick_yl', 'kick_result',
            'fg_dist', 'fg_result', 'xp_type', 'xp_result', 
            'retBy', 'ret_yards', 'ret_terr', 'ret_yl', 'tackler1', 'tackler2', 
            'fumble_num', 'fumbleBy', 'fumbleBy2', 'fumbleBy3', 
            'recoveredBy', 'recoveredBy2', 'recoveredBy3', 'recovery_team', 'recov_terr', 'recov_yl',
            'presnap_pen', 'penalty', 'penOn', 'pen_team', 'pen_yards',
            'touchdown', 'no_play', 'timeout', 'kneel', 'away_points_on_play', 'home_points_on_play', 
            'away_points', 'home_points']
view_cols = [col for col in view_cols if col in df.columns]
view = df[view_cols] 
view.to_csv('df_temp.csv')
export = view[view.play_type.str.len() > 0].copy()

gc = pd.to_datetime(export.game_clock, format = '%M:%S')
next_time = export.groupby('quarter')['game_clock'].shift(-1).fillna('00:00')
gcn = pd.to_datetime(next_time, format = '%M:%S')
grpBy = export.groupby(['quarter','game_clock'])
export['time_elapsed_next'] = gc - gcn
export['time_elapsed_chunk'] = grpBy['time_elapsed_next'].transform(max)
export['play_units'] = export.apply(play_duration, axis = 1)
export['play_units_chunk'] = grpBy['play_units'].transform(sum)
export['play_unit_duration'] = export.time_elapsed_chunk / export.play_units_chunk
export['play_duration'] = export.play_unit_duration * export.play_units
export['cum_play_duration'] = grpBy['play_duration'].cumsum().round('1s')
export['cum_play_duration'] = grpBy['cum_play_duration'].shift(1).fillna(datetime.timedelta(minutes = 0))
export['est_game_clock'] = gc - export['cum_play_duration']
export['sec_remaining_half'] = (export.est_game_clock.dt.minute*60 + export.est_game_clock.dt.second +
                                ((export.quarter % 2)*900))
export['est_game_clock'] = export['est_game_clock'].dt.strftime('%M:%S')
export['play_duration'] = (export['play_duration'].round('1s') + pd.to_datetime('1900/01/01')).dt.strftime('%M:%S')

export = export.drop(labels = ['time_elapsed_next', 'time_elapsed_chunk', 'play_units', 'play_units_chunk',
                                'play_unit_duration', 'cum_play_duration'], axis = 1)

away_pass = export[(export.poss == info_dict['away_abbr']) & (export.play_type == 'Pass')]

 
export.to_csv('sample_export.csv')


