# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 18:21:16 2023

@author: surma
"""

import pandas as pd
import numpy as np

def name_extract(str_ser,start_pattern,end_pattern, name_patterns, prefix = '', flags = 0):
    '''
    

    Parameters
    ----------
    df : dataframe with play_str from which substrings will be extracted
    phase_pattern : regex pattern that follows the name at the beginning of play_str
    *name_patterns : each name regex pattern to be applied

    Returns
    -------
    "overlayed" dataframe containing all extracted substrings

    '''
    patterns = [start_pattern + name_pattern + end_pattern for name_pattern in name_patterns]
    df_phase = str_ser.str.extract(patterns[0], flags = flags).fillna('')
    if len(patterns) > 1:
        for pattern in patterns[1:]:
            df_new = str_ser.str.extract(pattern, flags = flags).fillna('')
            for col in df_phase.columns:
                df_phase[col] = df_phase[col] + df_new[col]
    return df_phase.rename(columns = {name: prefix + name for name in ('first','last')})

def kick_extract(str_ser, kick_type, name_patterns):
    df_kicker = name_extract(str_ser, '^', f" {kick_type}", name_patterns, prefix ='kicker_')
    df_kicker['kick_type'] = np.where(df_kicker['kicker_first'].str.len() > 0, kick_type, '')
    df_yards = str_ser.str.extract(kick_type + " (?P<kick_yards>\d{1,2}) yard(?:s)?")
    yl_str = ".*? to the (?P<kick_terr>(?:[A-Z']+)?(?:\\d{4}|\\d{2})?)(?P<kick_yl>[0-9]{1,2})"
    df_yl = str_ser.str.extract(kick_type + yl_str)
    return pd.concat((df_kicker, df_yards, df_yl), axis = 1).fillna('')

def regex_check(df):
    df_check = df.replace('', np.NaN)
    return df_check.dropna(axis = 0, how = 'all')

def fumble_df(fum_str, name_patterns):
    df_fumBy = name_extract(fum_str, 'fumble by ', '', name_patterns, prefix = 'fumbleBy_')
    recov_by_pat = "recovered by (?P<recovery_team>[A-Z\d']+) "
    df_recov_by = name_extract(fum_str, recov_by_pat, '', name_patterns, prefix = 'recoveredBy_')
    recov_at_pat = " at (?P<recov_terr>(?:[A-Z']+)?(?:\\d{4}|\\d{2})?)(?P<recov_yl>[0-9]{1,2})"
    recov_yl = fum_str.str.extract(recov_at_pat)
    return pd.concat((df_fumBy, df_recov_by, recov_yl), axis = 1)

def possession(row, teams):
    if row['terr'] != '':
        other_side = [team for team in teams if team != row['terr']][0]
    else:
        other_side = ''
    if row['play_type'] in ['Run', 'Pass']:
        gain = 'gain_loss'
        to_yl = 'gnls_to_yl'
        to_terr = 'gnls_to_terr'
    elif row['play_type'] in ['Kickoff', 'Punt']:
        gain = 'kick_yards'
        to_yl = 'kick_yl'
        to_terr = 'kick_terr'
    elif row['play_type'] in ['FG', 'Extra Pt.', '2 Pt.']:
        return other_side
    else:
        return '' 
    if row[gain] > 0:
        if row['terr'] == row[to_terr]:
            if row['yl_raw'] < row[to_yl]:
                poss = row['terr']
            else:
                poss = other_side
        else:
            poss = row['terr']
    elif row[gain] < 0:
        if row['terr'] == row[to_terr]:
            if row['yl_raw'] > row[to_yl]:
                poss = row['terr']
            else:
                poss = other_side
        else:
            poss = row[to_terr]
    else:
        poss = ''
    return poss

def kick_result(row):
    if row['play_type'] in ('Punt', 'Kickoff'):
        if row['retBy'] != '' or row['recovery_team'] != '':
            return 'Return'
        else:
            for dex in ('fair_catch', 'out_of_bounds', 'touchback', 'downed'):
                if row[dex] == 1:
                    return (' '.join(dex.split(sep = '_'))).title()
    return ''

def possession_final(row, teams):
    # Possession can change in-play by fumble or blocked kick recovery, interception or return
    recoveries = [dex for dex in row.index if dex.startswith('recovery') and row[dex] != '']
    if len(recoveries) == 0:
        last_recovery_team = None
    elif len(recoveries) == 1:
        last_recovery_team = row[recoveries[0]]
    elif len(recoveries) > 1:
        last_recovery_team = row[sorted(recoveries)[-2]]
    if row['pass_result'] == 'Intercepted':
        int_team = [team for team in teams if row['poss'] != team][0]
    else:
        int_team = None
    if row['play_type'] in ('Extra Pt.', 'FG', 'Kickoff', 'Punt') and row['retBy'] != '':
        ret_team = [team for team in teams if row['poss'] != team][0]
    else:
        ret_team = None
    if not any((last_recovery_team, ret_team, int_team)):
        return row['poss']
    elif last_recovery_team and ret_team:
        return last_recovery_team
    elif last_recovery_team and int_team:
        recov_index = row['play_str'].find('recover')
        int_index = row['play_str'].find('intercept')
        if recov_index > int_index:
            return last_recovery_team
        else:
            return int_team 
    elif last_recovery_team:
        return last_recovery_team
    elif int_team:
        return int_team
    else:
        return ret_team
    
def points_on_play(row, team):
    if row['poss_final'] == team:
        if row['touchdown'] == 1:
            return 6
        if row['play_type'] == 'FG' and row['fg_result'] == 'Good':
            return 3
        if row['xp_result'] == 'Good':
            if row['xp_type'] == 'Kick':
                return 1
            else:
                return 2
        if row['def_pat'] == 1:
            return 2
    else:
        if row['safety'] == 1:
            return 2
    return 0

def time_remaining_half(row):
    min_sec = [int(unit) for unit in row['game_clock'].split(sep = ':')]
    sec_remaining = min_sec[0]*60 + min_sec[1]
    if row['quarter'] in (1,3):
        return sec_remaining + 900
    return sec_remaining

def play_duration(row):
    if row['play_type'] == 'Pass':
        return 1
    if row['play_type'] == 'Run':
        if row['timeout'] == 1:
            return 1
        elif row['touchdown'] == 1 and row['gain_loss'] < 20:
            return 1
        else:
            return 2
    if row['play_type'] == 'Kickoff':
        if row['kick_result'] == 'Return':
            return 1
        else:
            return 0
    if row['play_type'] in ('Extra Pt.', ''):
        return 0
    return 1
        
        
    