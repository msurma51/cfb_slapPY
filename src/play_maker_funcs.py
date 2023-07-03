# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 18:21:16 2023

@author: surma
"""

import pandas as pd

def name_extract(df,start_pattern,end_pattern,*name_patterns, prefix = ''):
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
    df_phase = df['play_str'].str.extract(patterns[0]).fillna('')
    if len(patterns) > 1:
        for pattern in patterns[1:]:
            df_new = df['play_str'].str.extract(pattern).fillna('')
            for col in df_phase.columns:
                df_phase[col] = df_phase[col] + df_new[col]
    return df_phase.rename(columns = {name: prefix + name for name in ('first','last')})