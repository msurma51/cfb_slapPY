# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 06:50:40 2023

@author: surma
"""

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
from play_maker_new import df
from play_maker_funcs import possession
import re

# Identify R/P/K play types
df['play_type'] = np.where(df.play_str.str.contains(' rush'), 'Run', 
                           np.where(df.pass_result != '', 'Pass', 
                                    np.where(df.kick_type != '', df.kick_type.str.capitalize(), 
                                             np.where(df.fg_result != '', 'FG', ''))))
# Fill / overwrite with XP plays
df['play_type'] = np.where(df.xp_type == 'kick', 'Extra Pt.', 
                           np.where(df.xp_type.isin(['rush', 'pass']), '2 Pt.', df.play_type))
# Fill with timeouts and pre-snap penalties
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
    loss = df[gain].str.extract('loss of (\d{1,2})').squeeze().fillna(0).astype('int64')
    gl = pd.Series(np.where(df[gain].str.contains('loss'), loss*-1, 
                            np.where(df[gain].str.contains('no'), 0, df[gain]))).astype('str')
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

for first_row, colname in zip(('qtr_first_row', 'drive_first_row'),('quarter', 'drive_num')):
    ser = df.groupby(first_row).cumcount()
    ser = np.where(df[first_row] == False, np.NaN, ser)
    df[colname] = (ser+1)
    df[colname] = df[colname].ffill().astype('int64')
df['drive_count'] = df.groupby('drive_num').cumcount()

first_cols = [col for col in df.columns if re.search('_first$', col)]
last_cols = [col for col in df.columns if re.search('_last$', col)]
name_cols = [col[:col.index('_last')] for col in last_cols]
df_name = pd.DataFrame()
for i, colname in enumerate(name_cols):
    name_col = df[[first_cols[i], last_cols[i]]].apply(' '.join, axis = 1).rename(colname)
    name_col = name_col.str.strip()
    df_name = pd.concat((df_name, name_col), axis = 1)
df_name['rusher'] = df_name.rusher.mask(df.try_type == 'Rush', df_name.xp)
df_name['passer'] = df_name.passer.mask(df.try_type == 'Pass', df_name.xp)
df_name['kicker'] = np.where(df.xp_type == 'kick', df_name.xp,
                             np.where(df.play_type == 'FG', df_name.fg, df_name.kicker))
df = pd.concat((df, df_name), axis = 1)


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

df['yl'] = np.where((df.terr == df.poss) & (df.yl_raw != 50), df.yl_raw * -1, df.yl_raw)
df['pen_yards'] = df.pen_yards.fillna(0).astype('int64')
for result_col in ('pass_result', 'fg_result', 'xp_type', 'xp_result', 'penalty'):
    df[result_col] = df[result_col].str.title()

view_cols = ['quarter', 'game_clock', 'drive_num', 'drive_count', 'poss', 'down', 'dist', 'yl', 'terr', 'play_type',
            'gain_loss', 'gnls_to_yl', 'gnls_to_terr', 'rusher', 'run_dir1', 'run_dir2', 
            'passer', 'pass_dir', 'intended', 'pass_result', 'intBy', 'int_terr', 'int_yl', 'pbuBy', 'hurriedBy',
            'kicker', 'kick_yards', 'kick_terr', 'kick_yl', 'fg_dist', 'fg_result', 'xp_type', 'xp_result', 
            'retBy', 'ret_yards', 'ret_terr', 'ret_yl', 'tackler1', 'tackler2', 
            'fumble_num', 'fumbleBy', 'fumbleBy2', 'fumbleBy3', 
            'recoveredBy', 'recoveredBy2', 'recoveredBy3', 'recovery_team', 'recov_terr', 'recov_yl',
            'presnap_pen', 'penalty', 'penOn', 'pen_team', 'pen_yards'
            'touchdown', 'no_play', 'timeout']
view_cols = [col for col in view_cols if col in df.columns]
view = df[view_cols] 
view.to_csv('df_temp.csv')
export = view[view.play_type.str.len() > 0]
export.to_csv('sample_export.csv')
