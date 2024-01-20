import re
# from pbp_parser import quarters, name_dict
from taster import quarters, name_dict
from hudl_namespace import *
from play_maker_hudl import *

# Initialize game state
game_state = {key:name_dict[key] for key in (home_name, away_name, home_abbr, away_abbr)}
game_start = {home_score: 0, away_score: 0, score_diff: 0, home_tol: 3,
              away_tol: 3, quarter: 1, time_stamp: '15:00',
              time_remaining: 1800}
game_state.update(game_start)
# Set name format for each team
re_select = dict()
re_select[name_dict[home_abbr]] = get_name_format(name_dict[home_kicker])
re_select[name_dict[away_abbr]] = get_name_format(name_dict[away_kicker])
# Determine coin toss results 
first_drive = quarters[0][0]
toss_info = toss_parser(first_drive,name_dict)
# If toss results are not available, find opening kick team another way
if len(toss_info) == 0:
    toss_info[open_kick] = possession_finder(first_drive,name_dict)
# Initialize object which will track possession throughout the game
ball = possession_tracker(name_dict[home_abbr],name_dict[away_abbr])
ot_ball = possession_tracker(name_dict[home_abbr],name_dict[away_abbr])
if toss_info[open_kick]:
    ball.set(toss_info[open_kick])
trackers = [0,0,0]
game = list()

def gb(drive):
    global name_dict, game_state, re_select, toss_info, ball, ot_ball, trackers, game
    j,i,o = trackers
    # Reset timeouts and possession at the start of the 3rd quarter
    if (i,j) == (2,0):
        game_state.update({home_tol: 3, away_tol: 3})
        poss = possession_finder(drive,name_dict)
        # If no possessor is found, set 2nd half kick team opposite 1st
        if not poss:
            ball.set(toss_info[open_kick])
            ball.flip()
        else:
            ball.set(poss) 
    # Reset timeout and set possession at the start of each overtime period
    elif i > 3:
        poss = possession_finder(drive,name_dict)                
        if j == 0:
            o = 1
            game_state.update({home_tol: 1, away_tol: 1, overtime: o})
        if poss:
            if poss == ot_ball.get():
                game_state.update({home_tol: 1, away_tol: 1})
                if j == 1:
                    j += -1
            ot_ball.set(poss)
        ball.set(ot_ball.get())
        if j > 0 and j % 2 == 0:
            o += 1
            game_state.update({overtime: o})
    # Run drive parser
    game_state[possession] = ball.get()
    plays = drive_parser(drive,game_state,re_select,i,j)
    # Check for unexpected splitting of the drive tables, except for Q3 start
    if h_start not in plays[0].keys() and not plays[0][q_start]:
        try:
            last_drive = game[-1]
            if play_type not in last_drive[-1].keys():
                for play in plays[1:]:
                    last_drive.append(play)
                plays = last_drive
                game.pop(-1)
        except:
            None
    # Determine drive end and update info
    info = plays[0]       
    info.update(drive_end_finder(plays))
    last_play = plays[-1]        
    # Don't flip possession on KO or Punt play when poss goes to kick team
    if fumble and fumble_poss in last_play.keys():    
        if last_play[fumble_poss] != ball.get():
            ball.flip()
    # Don't flip possession if the previous drive was the end of the quarter
    elif not info[drive_end] or info[drive_end] == end_quarter:
        None
    # Don't flip possession if the previous drive was a defensive or return TD
    elif last_play[possession] == ball.get():
        ball.flip()
    # If the drive is the start of 2nd or 4th quarter, merge it with the previous drive
    # unless the last play of the previous quarter was a drive-ending play
    if info[q_start] and i in (1,3):
        last_drive = game[-1]
        if not last_drive[0][drive_end] or last_drive[0][drive_end] == end_quarter:
            # Append plays individually at the end of last drive
            for play in plays[1:]:
                last_drive.append(play)
            # Update last drive info with q_start drive info
            last_drive[0][drive_end] = info[drive_end]
            if num_plays in info.keys():
                last_drive[0][num_plays] = info[num_plays]
            if total_yards in info.keys():
                last_drive[0][total_yards] = info[total_yards]
    else:
        game.append(plays)
    print(game[j])
    trackers[0] = j+1
    
x = iter(quarters[0])


