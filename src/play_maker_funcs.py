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
    yl_str = ".*? to the (?P<kick_terr>[A-Z\d']+?)(?P<kick_yl>[0-9]{1,2})"
    df_yl = str_ser.str.extract(kick_type + yl_str)
    return pd.concat((df_kicker, df_yards, df_yl), axis = 1)

def regex_check(df):
    df_check = df.replace('', np.NaN)
    return df_check.dropna(axis = 0, how = 'all')