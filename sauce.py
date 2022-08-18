# Sweat the veggies
from bs4 import BeautifulSoup   
import pandas as pd
import numpy as np
import os
from hudl_namespace import *
url = input('Enter -')
try:
    from pbp_parser_func import pbp_parser
    quarters, name_dict = pbp_parser(url)
except:
    from taster_func import taster
    quarters, name_dict = taster(url)  
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
        kicker, kick_yards, kick_to, kick_result, onside, punter, punt_yards, punt_to, punt_result, blocked_by,
        placekicker, fg_dist, fg_result, xp_result, two_point_attempt, taken_by, first_down, touchdown, no_play, nullified, safety,
        drive_end, time_stamp, time_remaining, off_score, def_score, pers_score_diff, pers_tol, off_tol, def_tol] + penalty_cols
for col in cols:
    if col not in df.columns:
        df[col] = np.NaN

         
def name_converter(player_name):
    # Converts names to standard 'First Last' format
    if player_name and ',' in player_name:
        last_first = player_name.split(sep = ',')
        return(last_first[1].strip() + ' ' + last_first[0])
    # Converts all TEAM captures to just TEAM (eliminating extra words captured)
    elif player_name and 'TEAM' in player_name:
        return('TEAM')
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
df_name_fields = [key for key in name_keys if key in df.columns]    
df[df_name_fields] = df[df_name_fields].applymap(name_converter, na_action='ignore')

# Determine whether user is scouting own team or opponent and which team is being scouted 
scout = input('Is this opponent scout? (Y/N)')
if scout.upper() in ('N','NO'):
    opp_scout = False
    scout_input = input('Are you {} (H) or {} (A)?'.format(name_dict[home_name],name_dict[away_name]))
else:
    opp_scout = True
    scout_input = input('Are you scouting {} (H) or {} (A)?'.format(name_dict[home_name],name_dict[away_name]))
# Based on the user input, determine to which team the input refers
home_caps = name_dict[home_name].upper()
away_caps = name_dict[away_name].upper()
if scout_input.upper() in ('H', home_caps):
    scout_team = name_dict[home_abbr]
elif scout_input.upper() in ('A', away_caps):
    scout_team = name_dict[away_abbr]
else:
    home_set = set(scout_input.upper()) & set(home_caps)
    away_set = set(scout_input.upper()) & set(away_caps)
    if len(home_set)/len(home_caps) > len(away_set)/len(away_caps):
        scout_team = name_dict[home_abbr]
    else:
        scout_team = name_dict[away_abbr]
if opp_scout:
    if scout_team == name_dict[home_abbr]:
        perspective = name_dict[away_abbr]
    else:
        perspective = name_dict[home_abbr]
else:
    perspective = scout_team
    
    
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
if opp_scout:
    if perspective == name_dict[home_abbr]:
        df[opp_team] = name_dict[home_name]
    else:
        df[opp_team] = name_dict[away_name]
    
    
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

# Print final score for fidelity check
print('Final score {} {} - {} {}'.format(name_dict[home_name], state[home_score], name_dict[away_name], state[away_score]))

# Check for incorrect possession ID by comparing home rushers and passers to those of the away team
home_df = df[df[possession] == name_dict[home_abbr]]
away_df = df[df[possession] == name_dict[away_abbr]]
home_players = set(home_df[passer]) | set(home_df[rusher])
away_players = set(away_df[passer]) | set(away_df[rusher])
overlap = home_players & away_players
overlap.discard(np.NaN)
overlap.discard('TEAM')
if overlap:
    print('Player name overlap detected in {}. Check possession transitions'.format(name_dict[matchup]))
   
# Export dataframe to csv with columns listed in the order of the 'cols' field label list
date_list = name_dict[game_date].split('/')
for i in range(2):
    if len(date_list[i]) < 2:
        date_list[i] = '0' + date_list[i]
date_str = '{}-{}-{}'.format(date_list[2],date_list[0],date_list[1])
if name_dict[scout_team] == name_dict[home_name]:
    game_str = '{} vs {}'.format(name_dict[home_name],name_dict[away_name])
else:
    game_str = '{} at {}'.format(name_dict[away_name],name_dict[home_name])

# Save to folder labelled with the name of the team being scouted
folder_name = input('Folder name? (Scout team name default)')
if len(folder_name) < 1:
    folder_name = name_dict[scout_team]
if not os.path.exists(folder_name):
    os.mkdir(folder_name)
df[cols].to_csv('{}\\{} {}.csv'.format(folder_name,date_str,game_str))