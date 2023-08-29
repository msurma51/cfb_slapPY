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
    fum_yl = fum_str.str.extract(recov_at_pat)
    df_fum_curr = pd.concat((df_fumBy, df_recov_by, fum_yl), axis = 1)
    return pd.concat((df_fumBy, df_recov_by, fum_yl), axis = 1)

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