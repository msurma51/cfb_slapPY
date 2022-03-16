from pbp_parser import *
from play_maker import *

# Initialize game state
game_state = {key:name_dict[key] for key in ('home_name', 'away_name', 'home_abbr', 'away_abbr')}
game_start = {'home_score': 0, 'away_score': 0, 'score_diff': 0, 'home_tol': 3,
              'away_tol': 3, 'quarter': 1, 'time_stamp': '15:00',
              'time_remaining': 1800}
game_state.update(game_start)
quarter = quarters[0]
# Determine coin toss results 
toss_info = toss_parser(quarter[0],name_dict)
# If toss results are not available, find the kicker who does the opening kickoff and
# match him with his team 
if len(toss_info) == 0:
    toss_info['open_kick'] = kicker_match(quarter[0][-1],name_dict)
# Set name format for each team
ball = possession(name_dict['home_abbr'],name_dict['away_abbr'])
re_select = dict()
re_select[name_dict['home_abbr']] = get_name_format(name_dict['home_kicker'])
re_select[name_dict['away_abbr']] = get_name_format(name_dict['away_kicker'])
# Process drives starting with opening kickoff
try:
    ball.set(toss_info['open_kick'])
except:
    None
game = list()
i,j = (0,0)
while i < len(quarters):
    quarter = quarters[i]
    for drive in quarter:
        # Reset timeouts and possession at the start of the 3rd quarter
        if (i,j) == (2,0):
            game_state.update({'home_tol': 3, 'away_tol': 3})
            poss = None
            for play in drive:
                receive = re.findall('([A-Z]+) will receive',play)
                if len(receive) > 0:
                    if receive[0] == name_dict['home_abbr']:
                        poss = name_dict['away_abbr']
                    else:
                        poss = name_dict['home_abbr']
                    break
            if not poss:
                for play in drive:
                    has_ball = re.findall('([A-Z]+) ball',play)
                    if len(has_ball) > 0:
                        poss = has_ball[0]
                        break
            if not poss:
                kick_team = kicker_match(drive[-1],name_dict)
                if kick_team:
                    poss = kick_team
            if not poss:
                ball.set(toss_info['open_kick'])
                ball.flip()
            else:
                ball.set(poss) 
            j += 1
        # Run drive parser
        game_state['possession'] = ball.get()
        plays = drive_parser(drive,game_state,re_select)
        # Check for unexpected splitting of the drive tables, except for Q3 start
        if 'h_start' not in plays[0].keys() and not plays[0]['q_start']:
            try:
                last_drive = game[-1]
                if 'type' not in last_drive[-1].keys():
                    for play in plays[1:]:
                        last_drive.append(play)
                    plays = last_drive
                    game.pop(-1)
            except:
                None
        # Determine drive end and update info
        info = plays[0]       
        info.update(drive_end(plays))
        last_play = plays[-1]        
        # Don't flip possession on KO or Punt play when poss goes to kick team
        if 'fumble' and 'fumble_poss' in last_play.keys():    
            if last_play['fumble_poss'] != ball.get():
                ball.flip()
        # Don't flip possession if the previous drive was the end of the quarter
        elif not info['drive_end'] or info['drive_end'] == 'Quarter':
            None
        # Don't flip possession if the previous drive was a defensive or return TD
        elif last_play['possession'] == ball.get():
            ball.flip()
        # If the drive is the start of 2nd or 4th quarter, merge it with the previous drive
        # unless the last play of the previous quarter was a drive-ending play
        if info['q_start'] and i in (1,3):
            last_drive = game[-1]
            if not last_drive[0]['drive_end'] or last_drive[0]['drive_end'] == 'Quarter':
                # Append plays individually at the end of last drive
                for play in plays[1:]:
                    last_drive.append(play)
                # Update last drive info with q_start drive info
                last_drive[0]['drive_end'] = info['drive_end']
                if 'num_plays' in info.keys():
                    last_drive[0]['num_plays'] = info['num_plays']
                if 'total_yards' in info.keys():
                    last_drive[0]['total_yards'] = info['total_yards']
        else:
            game.append(plays)
    i += 1

    
