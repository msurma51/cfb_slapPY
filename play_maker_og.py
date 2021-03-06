import re

def get_name_format(player_name):
    name_re = "([\w'-]+,[\w'-]+)"
    if player_name.find(',') == -1:
        name_re = "([\w'-]+.* [\w'-]+)"
    elif player_name.find(" ") >-1:
        name_re = "([\w'-]+, [\w'-]+)"
    return(name_re)

def drive_dex(pattern, drive_strings):
    for i in range(len(drive_strings)):
        found = re.findall(pattern,drive_strings[i],re.IGNORECASE)
        if len(found) > 0:
            return((i,found[0]))
    return(None)


def ddyl_parser(string,poss):
    ddyl = dict()
    down = re.findall('([1-4])[a-z]+',string)
    distance = re.findall(' [0-9]+ ',string)
    yl_split = re.findall('([A-Z]+)([0-9]+)',string)
    if string == 'Opening kickoff':
        ddyl['open_kick'] = True
        return(ddyl)
    try:
        ddyl['down'] = int(down[0])
    except:
        return(ddyl)
    try:
        yl = int(yl_split[0][1])
        # Determine whether offense is in their own territory
        if yl_split[0][0] == poss:
            yl = yl*(-1)
        ddyl['yard line'] = yl
    except:
        None
    try:
        ddyl['distance'] = int(distance[0])
    except:
        goal_to_go = re.search(' GOAL ', string, re.IGNORECASE)
        if goal_to_go:
            ddyl['distance'] = yl
    return(ddyl)



def time_conv(t_string,quarter):
    m_s = t_string.split(sep=":")
    time_remaining = int(m_s[0])*60+int(m_s[1])
    if quarter in (1,3):
        time_remaining += 900
    return(time_remaining)



def add_tacklers(play,desc):
    para_dex = desc.find('(')
    pen_dex = desc.find('PENALTY')
    # Check for no potential tacklers
    if para_dex == -1:
        return(play)
    # Check if players in parentheses are penalized and not tacklers
    elif pen_dex != -1 and para_dex > pen_dex:
        return(play)
    tacklers = re.findall('\((.*?)\)',desc)[0].split('; ')
    play['tackler1'] = tacklers[0]
    if len(tacklers) >1:
        play['tackler2'] = tacklers[1]
    return(play)


def add_fumble(play,poss,f_string,name_re,fumble_n):
    fum_keys = ['fumbled_by', 'recover_team', 'recovered_by',
                'forced_by']
    if fumble_n > 1:
        for i in range(len(fum_keys)):
            fum_keys[i] = fum_keys[i] + str(fumble_n)
    fumbler = re.findall("fumble.* by " + name_re,f_string)
    if len(fumbler) > 0:
        play[fum_keys[0]] = fumbler[0]
    recovery = re.findall("recovered by ([A-Z]+) " + name_re,f_string)
    if len(recovery) > 0:
        play[fum_keys[1]] = recovery[0][0]
        play[fum_keys[2]] = recovery[0][1]
    forced = re.findall("fumble forced by " + name_re,f_string)
    if len(forced) >0:
        play[fum_keys[3]] = forced[0]
    play['fumble_count'] = fumble_n
    play['fumble_poss'] = play[fum_keys[1]]
    fum_return = f_string.find(' return')
    if fum_return > -1:
        r_string = f_string[fum_return:]
        play = add_return(play,r_string,poss,name_re)
    return(play)



def add_penalty(play,desc,name_re):
    # Consider only the text after 'PENALTY' and before first yard line mentioned
    pen_str = desc[desc.find('PENALTY'):]
    stop = re.search('[A-Z]+[0-9]+',pen_str)
    if stop:
        pen_str = pen_str[:pen_str.find(stop.group())]
    team = re.findall(' ([A-Z]+) ',pen_str)
    # Consider all possible penalties (potentially multiple for either team)
    for i in range(len(team)):
        team_key = 'pen_team' + str(i+1)
        play[team_key] = team[i]
        penalty = re.findall(play[team_key] + ' (.*?) \(',pen_str)
        if len(penalty) == 0:
            penalty = re.findall(play[team_key] + ' (.*?) [0-9]',pen_str)
        try:
            pen_key = 'penalty' + str(i+1)
            play[pen_key] = penalty[i]
        except:
            None
        against = re.findall('\(' + name_re + '\)',pen_str)
        try:
            against_key = 'against' + str(i+1)
            play[against_key] = against[i]
        except:
            None
    pen_yards = re.findall(' ([0-9]+) ',pen_str)
    try:
        play['pen_yards'] = int(pen_yards[0])
    except:
        None
    return(play)



def add_return(play,r_string,poss,name_re):
    returner = re.search(" " + name_re + " ",r_string)
    if returner:
        play['returner'] = returner.group()
    ret_yards = re.findall(' ([0-9]+) yards',r_string)
    try:
        play['ret_yards'] = ret_yards[0]
    except:
        None
    return_yl = re.findall('([A-Z]+)([0-9]+)',r_string)
    if len(return_yl) > 0:
        play['ret_territory'] = return_yl[0][0]
        return_to = int(return_yl[0][1])
        if play['ret_territory'] == poss:
            return_to = return_to*(-1)
        play['return_to'] = return_to
    return(play)
        
    


def run_parser(play,desc,name_re):
    play['type'] = 'Run'
    try:
        play['rusher'] = re.findall('^' + name_re,desc)[0]
    except:
        None
    gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])
    if desc.find(" loss ") > -1:
        gain_loss = gain_loss*(-1)
    play['gain\\loss'] = gain_loss
    return(play)



def pass_parser(play,desc,poss,name_re):
    play['type'] = 'Pass'
    try:
        play['passer'] = re.findall('^' + name_re,desc)[0]
    except:
        None
    gain_loss = 0
    if desc.find(" incomplete ") > -1:
        play['pass_result'] = "Incomplete"
    if desc.find(" complete ") > -1:
        gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])
        play['pass_result'] = "Complete"
    if desc.find(" sacked ") > -1:
        gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])*(-1)
        play['pass_result'] = "Sack"
    play['gain\\loss'] = gain_loss
    # Determine intended WR and whether QB was intercepted or hurried
    intended = re.findall("complete to " + name_re,desc)
    if len(intended) > 0:
        play['intended'] = intended[0]
    intercepted = re.findall("intercepted by " + name_re,desc)
    if len(intercepted) > 0:
        play['pass_result'] = "Interception"
        play['intercepted_by'] = intercepted[0]
        int_return = desc.find('return')
        if int_return > -1:
            r_string = desc[int_return:]
            play = add_return(play,r_string,poss,name_re)
    hurried = re.findall("QB hurried by " + name_re,desc)
    if len(hurried) > 0:
        play['hurried_by'] = hurried[0]
    pbu = re.findall("broken up by " + name_re,desc)
    if len(pbu) > 0:
        play['broken_up_by'] = pbu[0]
    return(play)



def kop_parser(play,desc,poss,name_re):
    if desc.find('punt') > -1:
        ktype = 'punt'
        k_keys = ('punter','punt_yards','punt_to','punt_result')
    else:
        ktype = 'kickoff'
        k_keys = ('kicker','kick_yards','kick_to','kick_result')
    play['type'] = ktype.title()
    # First consider the string segment containing kick info
    kick_yl = re.search('[A-Z]+[0-9]+',desc)
    k_string = desc[:kick_yl.span()[1]]
    # Extract the kicker's name if it's there
    if k_string.find(ktype) > 0:
        kp = re.findall('^'+name_re,k_string)
        try:
            play[k_keys[0]] = kp[0]
        except:
            None
    yards = re.findall(ktype + ' ([0-9]+) yards',k_string)
    try:
        play[k_keys[1]] = int(yards[0])
    except:
        None
    # Split team name from numerical yl
    yl_split = re.findall('([A-Z]+)([0-9]+)',kick_yl.group())[0]
    kick_to = int(yl_split[1])
    if yl_split[0] == poss:
        kick_to = kick_to*(-1)
    play[k_keys[2]] = kick_to
    # Now consider the end of the string, either kick result or return
    r_string = desc[kick_yl.span()[1]:]
    if r_string.find('return') > -1:
        play = add_return(play,r_string,poss,name_re)
    else:
        for kick_result in ['fair catch','Touchback', 'out-of-bounds']:
            if r_string.find(kick_result) > -1:
                play[k_keys[3]] = kick_result
                break
    return(play)



def fg_parser(play,desc,poss,name_re):
    fg = desc.find('field goal')
    if fg > -1: 
        play['type'] = 'FG'
        res_key = 'fg_result'
        kick_dist = re.findall(' [0-9]{2} ',desc)
        try:
            play['fg_dist'] = int(kick_dist[0])
        except:
            None
    else:
        play['type'] = 'XP'
        res_key = 'xp_result'
        fg = desc.find('kick attempt')
    # Extract the placekicker's name if it's there
    if fg > 0:
        pk = re.findall('^'+name_re,desc)
        try:
            play['placekicker'] = pk[0]
        except:
            None   
    result_string = desc[desc.find('attempt'):]
    good = re.search('[A-Z]+ GOOD',result_string,re.IGNORECASE)
    if good:
        if re.search('NO',good.group(),re.IGNORECASE):
            play[res_key] = 'No Good'
        else:
            play[res_key] = 'Good'
    elif re.search(' blocked ',result_string,re.IGNORECASE):
        play[res_key] = 'Blocked'
    fg_return = result_string.find('return')
    if fg_return > -1:
        r_string = result_string[fg_return:]
        play = add_return(play,r_string,poss,name_re)
    return(play)



def try_parser(play,desc,name_re):
    try_name = re.findall('^' + name_re,desc)
    if desc.find(' rush ') >-1:
        play['type'] = 'Run'
        try:
            play['rusher'] = try_name[0]
        except:
            None
    else:
        play['type'] = 'Pass'
        try:
            play['passer'] = try_name[0]
        except:
            None        
    if re.search(' failed',desc,re.IGNORECASE):
        play['two_point_attempt'] = 'No Good'
    else:
        play['two_point_attempt'] = 'Good'
    return(play)
        


def timeout_parser(play,desc):
    play['type'] = 'Timeout'
    team = re.findall('Timeout ([A-Z]+)', desc, re.IGNORECASE)
    try:
        play['taken_by'] = team[0]
    except:
        None
    return(play)



def end_parser(desc):
    end = dict()
    # Extract the play and total yard counts
    term_dict = {"play" : "num_plays", "yard" : "total_yards"}
    for term in term_dict.keys():
        amount = re.findall("(\S*[0-9]+) " + term,desc)
        try:
            end[term_dict[term]] = int(amount[0])
        except:
            None
    time_elapsed = re.search("[0-9]+:[0-9]{2}",desc)
    if time_elapsed:
        end['time_of_possession'] = time_elapsed.group()
        end['time_elapsed_sec'] = time_conv(time_elapsed.group(),2)
    if desc.find(' game') >-1:
        end['drive_end'] = 'Game'
    elif desc.find(' half') >-1:
        end['drive_end'] = 'Half'
    elif desc.find(' quarter') >-1:
        end['drive_end'] = 'Quarter'
    return(end)



def score_update(home_ball,points,play_state):
    if home_ball:
        play_state['home_score'] += points
    else:
        play_state['away_score'] += points
    play_state['score_diff'] = play_state['home_score'] - play_state['away_score']
    return(play_state)



def state_update(play,poss,desc,play_state):
    # Determine whether the home team has possession in order to know which side to add/deduct from
    home_ball = poss == play_state['home_abbr']
    if 'touchdown' in play.keys():
        if 'fumble_poss' in play.keys() and play['fumble_poss'] != poss:
            play_state.update(score_update(not home_ball,6,play_state))
        elif 'pass_result' in play.keys() and play['pass_result'] == 'Interception':
            play_state.update(score_update(not home_ball,6,play_state))
        else:
            play_state.update(score_update(home_ball,6,play_state))
    if 'xp_result' in play.keys() and play['xp_result'] == 'Good':
        play_state.update(score_update(home_ball,1,play_state))
    elif 'two_point_att' in play.keys() and play['two_point_att'] == 'Good':
        play_state.update(score_update(home_ball,2,play_state))
    elif 'fg_result' in play.keys() and play['fg_result'] == 'Good':
        play_state.update(score_update(home_ball,3,play_state))
    if 'safety' in play.keys() and play['safety']:
        play_state.update(score_update(not home_ball,2,play_state))
    if 'type' in play.keys() and play['type'] == 'Timeout':
        try:
            if play['taken_by'] == play_state['home_abbr']:
                play_state['home_tol'] += -1
            elif play['taken_by'] == play_state['away_abbr']:
                play_state['away_tol'] += -1
        except:
            None
    clock = re.search('[0-9]+:[0-9]{2}', desc)
    if clock:
        time = clock.group()
        play_state['time_stamp'] = time
        play_state['time_remaining'] = time_conv(time,play_state['quarter'])
    return(play_state)



class possession:
    count = 0
    'Stores and tracks possession throughout game parsing'
    def __init__(self,home_team,away_team):
        self.home = home_team
        self.away = away_team
        self.teams = (home_team,away_team)
        self.ball = None
    def set(self,poss_team):
        if poss_team in self.teams:
            self.ball = poss_team
    def get(self):
        return(self.ball)
    def flip(self):
        if self.ball == self.home:
            self.ball = self.away
            possession.count += 1
        elif self.ball == self.away:
            self.ball = self.home
            possession.count += 1



def drive_end(plays):
    end_dict = dict()
    end = None
    if 'h_start' in plays[0].keys():
        end = 'Opening Kick'         
    elif plays[-1]['type'] == 'Kickoff':
        if 'q_start' in plays[-2].keys():
            return(end_dict)
        elif plays[-2]['type'] == 'XP' or 'two_point_attempt' in plays[-2].keys():


            end = 'TD'
        elif plays[-2]['type'] == 'FG':
            end = 'FG'
    elif plays[-1]['type'] == 'Punt':
        end = 'Punt'
    elif plays[-1]['type'] == 'FG':
        if plays[-1]['fg_result'] == 'No Good':
            end = 'Missed FG'
        elif plays[-1]['quarter'] in (1,3):
            end = 'FG'
        elif plays[-1]['quarter'] == 2:
            end = 'Half'
        else:
            end = 'Game'
    elif 'fumble' in plays[-1].keys():
        end = 'Fumble'
    elif 'pass_result' in plays[-1].keys() and plays[-1]['pass_result'] == 'Interception':
        end = 'Interception'
    elif 'gain\\loss' in plays[-1].keys() and plays[-1]['down'] == 4:
        if plays[-1]['gain\\loss'] < plays[-1]['distance']:
             end = 'Downs'
    end_dict['drive_end'] = end
    return(end_dict)
        
        
    
        
        


def toss_parser(drive0,name_dict):
    toss_dict = dict()
    # If a coin toss string exists, find it and extract relevant info
    toss_string = None
    for string in drive0:
        if string.find(' toss') >-1:
            toss_string = string
            break
    if toss_string:
        winner = re.findall('^(\w+) wins toss',toss_string)
        if len(winner) > 0:
            defer = toss_string.find(' defer')
            receive = toss_string.find(' receive')
            if winner[0] in name_dict['home_name'] or winner[0] in name_dict['home_abbr']:
                toss_dict['won_toss'] = name_dict['home_abbr']
                loser = name_dict['away_abbr']
            else:
                toss_dict['won_toss'] = name_dict['away_abbr']
                loser = name_dict['home_abbr']
            if defer >-1:
                toss_dict['winner_choice'] = 'defer'
                if receive >-1:
                    toss_dict['loser_choice'] = 'receive'
                    toss_dict['open_kick'] = toss_dict['won_toss']
                else:
                    toss_dict['loser_choice'] = 'kick'
                    toss_dict['open_kick'] = loser
            elif receive >-1:
                toss_dict['winner_choice'] = 'receive'
                toss_dict['open_kick'] = loser
            else:
                toss_dict['winner_choice'] = 'kick'
                toss_dict['open_kick'] = toss_dict['won_toss']
    return(toss_dict)



def kicker_match(string,name_dict):
    kicker = re.findall('^(.*)kickoff', string)
    kick_team = None
    if len(kicker)>0:
        if name_dict['away_kicker'] in kicker[0]:
            kick_team = name_dict['away_abbr']
        elif name_dict['home_kicker'] in kicker[0]:
            kick_team = name_dict['home_abbr']
    return(kick_team)
        
    
        
def play_parser(string_list,poss,name_re):
    play = ddyl_parser(string_list[0],poss)
    desc = string_list[1]
    # Drive end string
    if not play:
        play = end_parser(desc)
        return(play)
    # 2 point attempt
    elif desc.find("rush attempt ") >-1 or desc.find("pass attempt ") >-1:
        play = try_parser(play,desc,name_re)
        return(play)
    # Run
    elif desc.find(" rush ") >-1 or desc.startswith("rush "):
        play = run_parser(play,desc,name_re)
    # Pass
    elif desc.find(" pass ") > -1 or desc.startswith('pass ') or desc.find(" sacked ") > -1:
        play = pass_parser(play,desc,poss,name_re)
    # Pre-snap penalty
    elif desc.startswith("PENALTY"):
        play['type'] = 'Penalty'
        play = add_penalty(play,desc,name_re)
        return(play)
    # Timeout
    elif re.search('Timeout ', desc, re.IGNORECASE):
        play = timeout_parser(play,desc)
        return(play)
    # Kickoff / punt
    elif desc.find('kickoff') > -1 or desc.find('punt') > -1:
        play = kop_parser(play,desc,poss,name_re)
    # Extra point / field goal
    elif desc.find("field goal") > -1 or desc.find('kick attempt') > -1:
        play = fg_parser(play,desc,poss,name_re)
    # Kneel
    elif desc.startswith("Kneel "):
        play = run_parser(play,desc,name_re)
        play['type'] = 'Kneel'
        return(play)
    # Add tacklers
    play = add_tacklers(play,desc)
    # Add every fumble
    fumble = desc.find(' fumble')
    fumble_n = 0
    f_string = desc
    while fumble > -1:
        fumble_n += 1
        f_string = f_string[fumble:]
        play = add_fumble(play,poss,f_string,name_re,fumble_n)
        f_string = f_string[7:]
        fumble = f_string.find(' fumble')
    # Add post-snap penalty
    if desc.find(' PENALTY ') > -1:
        play = add_penalty(play,desc,name_re)
    # Add result
    result_dict = {" TOUCHDOWN":"touchdown", " NO PLAY": "no_play",
                   " 1ST DOWN": "first_down", " safety": "safety",
                   " fumble": "fumble"}
    for key in result_dict.keys():
        if re.search(key,desc,re.IGNORECASE):
            play[result_dict[key]] = True   
    return(play)
    
    


def drive_parser(drive_strings, poss, game_state, name_re):
    plays = list()
    # Dictionary to store drive info...
    info = {key:game_state[key] for key in game_state.keys() if key != 'time_stamp'}
    # ...stored as the '0' play of the drive
    plays.append(info)
    # Can check possession by passing in name_dict and parsing initial strings
    info['possession'] = poss
    start = 0
    h = drive_dex('Start of ([1-4]).*Half',drive_strings)
    q = drive_dex('Start of ([1-4]).*quarter',drive_strings)
    if h and not q:
        q = (-1,2*int(h[1])-1)
    ds = drive_dex('drive start', drive_strings)
    # Determine whether the "drive" is the start of a quarter
    if q:
        # Set the quarter
        info['quarter'] = int(q[1])
        info['q_start'] = True
        # New quarter = start time of '15:00'
        info['drive_start'] = '15:00'
        # Determine the start of plays to parse
        start = q[0]+1
        if h:
            info['h_start'] = True
            info['time_remaining'] = time_conv(info['drive_start'],info['quarter'])
            game_state.update({'quarter': info['quarter'],
                   'time_stamp': info['drive_start'],
                   'time_remaining': info['time_remaining']})
            plays.append(play_parser(['Opening kickoff',drive_strings[-1]],poss,name_re))
            return(plays)
        if ds:
            start = ds[0]+1
    else:
        info['q_start'] = False
        # Set drive start time
        info['drive_start'] = game_state['time_stamp']
        for i in range(len(drive_strings)):
            times = re.findall('[0-9]+:[0-9]{2}',drive_strings[i])
            if len(times) > 0:
                info['drive_start'] = times[0]
                break
        # String after 'drive start' begins plays
        if ds:
            start = ds[0]+1
        else:
            start = drive_dex('^1',drive_strings)[0]    
    info['time_remaining'] = time_conv(info['drive_start'],info['quarter'])
    game_state.update({'quarter': info['quarter'],
                       'time_stamp': info['drive_start'],
                       'time_remaining': info['time_remaining'],
                       'home_tol': info['home_tol'],
                       'away_tol': info['away_tol']})
    while start < len(drive_strings)-1:
        play = play_parser(drive_strings[start:start+2],poss,name_re)
        if play and 'type' in play.keys():
            play.update(game_state)
            plays.append(play)
            game_state = state_update(play,poss,drive_strings[start+1],game_state)
        else:
            info.update(play)
        start += 2
    return(plays)
    
    

def game_builder(quarters,name_dict):
    # Initialize game state
    game_state = {key:name_dict[key] for key in ('home_abbr', 'away_abbr')}
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
            plays = drive_parser(drive,ball.get(),game_state,re_select[ball.get()])
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
                    # Append plays at the end of last drive
                    last_drive.append(plays[1:])
                    # Update last drive info with q_start drive info
                    last_drive[0]['drive_end'] = info['drive_end']
                    if 'num_plays' in info.keys():
                        last_drive[0]['num_plays'] = info['num_plays']
                    if 'total_yards' in info.keys():
                        last_drive[0]['total_yards'] = info['total_yards']
            else:
                game.append(plays)
        i += 1
    return(game,game_state)
    


