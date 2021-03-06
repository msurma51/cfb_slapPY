# Sweat the veggies
import pandas as pd
import numpy as np
from hudl_namespace import *
from pbp_parser import quarters, name_dict
from play_maker_hudl import game_builder
game_info = game_builder(quarters,name_dict)
game = game_info['game']
state = game_info['state']
# Add the drive end value to the last offensive play run on each drive
for drive in game:
    for i in range(len(drive)-1):
        if drive[-(i+1)][play_type] in (type_run, type_pass):
            drive[-(i+1)].update({drive_end:drive[0][drive_end]})
            break
# List each play sequentially, eliminating drive info dictionary for each drive
plays = [play for drive in game for play in drive if play != drive[0]]
# Create index for dataframe such that each play has an index of the play number
dex = pd.Series(list(range(1,len(plays)+1)),name = 'PLAY #')
df = pd.DataFrame(plays, index = dex)

# Create a list of columns desired for each dataframe. Will be presented in order in the csv export
penalty_keys = [penalty, pen_team, against]
penalty_cols = [key + '1' for key in penalty_keys] + [key + '2' for key in penalty_keys] + [pen_yards]
cols = [opp_team, odk, possession, quarter, overtime, series, series_num, down, distance, yard_line, play_type, play_result, gn_ls, 
        rusher, passer, pass_result, intended, broken_up_by, intercepted_by, hurried_by, tackler1, tackler2,
        fumble, fumbled_by, forced_by, recover_team, recovered_by, returner, ret_yards, return_to,        
        kicker, kick_yards, kick_to, kick_result, punter, punt_yards, punt_to, punt_result,
        placekicker, fg_dist, fg_result, xp_result, two_point_attempt, taken_by, first_down, touchdown, no_play, safety,
        drive_end, time_stamp, time_remaining, off_score, def_score, pers_score_diff, pers_tol, off_tol, def_tol] + penalty_cols
for col in cols:
    if col not in df.columns:
        df[col] = np.NaN

name_keys = [rusher,passer,intended,kicker,placekicker,punter,returner,tackler1,tackler2,
             fumbled_by,fumbled_by + '2',recovered_by,recovered_by + '2', forced_by, hurried_by,
             broken_up_by,intercepted_by,against + '1',against + '2']
             
def name_converter(player_name):
    # Converts names to standard 'First Last' format
    if player_name and ',' in player_name:
        last_first = player_name.split(sep = ',')
        return(last_first[1].strip() + ' ' + last_first[0])
    else:
        return(player_name)
        
def odk_maker(play,perspective):
    # Determines ODK based on play type and perspective
    if play[play_type] in (type_run, type_pass):
        if play[possession] == perspective:
            return('O')
        else: 
            return('D')
    elif play[play_type] in (timeout, type_penalty, type_kneel):
        return(None)
    else:
        return('K')
        
def od_score_tol(play):
    # Determines timeouts left for each team based on O/D using home/away and possession
    if play[possession] == play[home_abbr]:
        return([play[home_score],play[away_score],play[home_tol],play[away_tol]])
    else:
        return([play[away_score],play[home_score],play[away_tol],play[home_tol]])
        
def k_types(play, perspective):
    # Renames kick play types to those used by Hudl based on perspective
    if play[play_type] in (type_kickoff, type_punt, type_fg, type_xp) and play[possession] != perspective:
        if play[play_type] in (type_kickoff, type_punt):
            return(play[play_type] + ' Ret')
        else:
            return(play[play_type] + ' Block')
    else:
        return(play[play_type])
    
def result_maker(play):
    # Determines Hudl 'Result' value for each play using individual result values from dataframe
    k_map = {type_fg: fg_result, type_xp: xp_result, type_kickoff: kick_result, type_punt: punt_result}
    if play[play_type] in k_map.keys():
        return(play[k_map[play[play_type]]])
    elif not pd.isna(play[two_point_attempt]):
        return(play[two_point_attempt])
    elif play[play_type] == type_pass:
        return(play[pass_result])
    elif play[play_type] == type_run:
        return('Rush')
    else:
        return(play[play_type])

# Convert names to standard 'First Last' format    
df[name_keys] = df[name_keys].applymap(name_converter, na_action='ignore')

# Get perspective as a user input
perspective = input('Perspective: {} (H) or {} (A)?'.format(name_dict[home_abbr],name_dict[away_abbr]))
if perspective.upper() == 'A':
    perspective = name_dict[away_abbr]
# If 'A' or away abbreviation is not the input, default to home team
elif perspective not in name_dict.values():
    perspective = name_dict[home_abbr]
# Apply result function to dataframe, filling Hudl 'RESULT' column
df[play_result] = df.apply(result_maker, axis=1)
# For points after, replace potentially erroneous distance listed with the actual yard line
df[distance].mask((df[play_type] == type_xp) | ~(pd.isna(df[two_point_attempt])), df[yard_line], inplace = True)
# Apply ODK function to fill that column
df[odk] = df.apply(odk_maker, axis=1, args=(perspective,))
# Change kick play types to Hudl names based on perspective
df[play_type] = df.apply(k_types, axis=1, args=(perspective,))
# Fill score columns to track current scores for O and D based on perspective
df[[off_score,def_score,off_tol,def_tol]] = df.apply(od_score_tol, axis=1, result_type='expand')
# Use perspective input to determine score diff, timeouts left and opposing team for scouting team
if perspective == name_dict[home_abbr]:
    df[pers_score_diff] = df[score_diff]
    df[pers_tol] = df[home_tol]
    df[opp_team] = df[away_name]
else:
    df[pers_score_diff] = df[score_diff]*-1
    df[pers_tol] = df[away_tol]
    df[opp_team] = df[home_name]
scout_team = input('Is this opponent scout? (Y/N)')
''' If input indicates opponent scout, opposing team will be set to perspective.
 I.e. if Ohio State is scouting Penn State using PSU vs. ILL, Ohio State should select 'ILL' as the
 perspective. OPP TEAM would then be ILL. However, if Penn State were using the same game to self-scout,
 'PSU' would be selected as perspective but OPP TEAM would still be ILL.
'''
if scout_team.upper() not in ('N','NO'):
    df[opp_team] = perspective
    
    
# Count series numbers for O and D and track the play number within each series. Store these values
# in a sequential list to be added to the dataframe at the end.
# Each overtime series is considered a separate series
o_series, d_series, play_count = (0,0,0)
series_list, series_num_list = ([],[])
(prev_odk,prev_ot) = (None,np.nan)
for index, row in df.iterrows():
    if row[odk] == 'K' or not row[odk]:
        series_list.append(None)
        series_num_list.append(None)
    elif row[odk] != prev_odk or all((row[overtime] > 0,row[overtime] != prev_ot)):
        play_count = 1
        series_num_list.append(play_count)
        if row[odk] == 'O':
            o_series += 1
            series_list.append(o_series)
        else:
            d_series += 1
            series_list.append(d_series)
    else:
        play_count += 1
        series_num_list.append(play_count)
        if row[odk] == 'O':
            series_list.append(o_series)
        else:
            series_list.append(d_series)  
    if row[odk]:
        prev_odk = row[odk]
        prev_ot = row[overtime]       
df[[series,series_num]] = pd.Series([series_list,series_num_list])
# Change the first play of each drive and two point attempts to '0'th down for analysis purposes
df[down].mask((df[series_num]==1) | ~(pd.isna(df[two_point_attempt])), 0, inplace = True)
   
#Export dataframe to csv with columns listed in the order of the 'cols' field label list   
df[cols].to_csv('pete_test.csv')