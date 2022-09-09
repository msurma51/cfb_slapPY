import re
import traceback
from hudl_namespace import *

def get_name_format(player_name):
    name_re = "([\w'-]+,*(?: Jr)*[.]*,[\w'-]+)"
    if player_name.find(',') == -1:
        name_re = "([\w'-.]+ [\w'-]+)"
    elif player_name.find(" ") >-1:
        name_re = "([\w'-]+, [\w'-]+)"
    return(name_re)
    
def name_check(play, name_keys):
    name_key_list = [key for key in name_keys if key in play.keys()]
    matches = dict()
    for name_key in name_key_list:
        dex = play[name_key].find(',')
        if dex > -1:
            if play[name_key][dex+1] == ' ':
                matches[name_key] = play[name_key]
            else:
                matches[name_key] = play[name_key].split()[0]
    return(matches)
    

def drive_dex(pattern, drive):
    for i in range(len(drive)):
        found = re.findall(pattern,drive[i][-1],re.IGNORECASE)
        if len(found) > 0:
            return((i,found[0]))
    return(None)


def ddyl_parser(string,poss):
    ddyl = dict()
    dn = re.findall('([1-4])[a-z]+',string)
    dis = re.findall(' [0-9]+ ',string)
    yl_split = re.findall('([A-Z]+)([0-9]+)',string)
    if string == 'Opening kickoff':
        ddyl[open_kick] = True
        return(ddyl)
    try:
        ddyl[down] = int(dn[0])
    except:
        return(ddyl)
    try:
        yl_string = yl_split[0][1]
        if len(yl_string) > 2:
            yl = int(yl_string[-2:])
        else:
            yl = int(yl_string)
        # Determine whether offense is in their own territory
        if yl_split[0][0] == poss:
            yl = yl*(-1)
        ddyl[yard_line] = yl
    except:
        None
    try:
        ddyl[distance] = int(dis[0])
    except:
        goal_to_go = re.search(' GOAL ', string, re.IGNORECASE)
        if goal_to_go:
            ddyl[distance] = yl
    return(ddyl)



def time_conv(t_string,quarter):
    m_s = t_string.split(sep=":")
    time_remaining = int(m_s[0])*60+int(m_s[1])
    if quarter in (1,3):
        time_remaining += 900
    return(time_remaining)



def sec_to_min(sec):
    min_string = '{}:{}'.format(sec//60,sec%60)
    return(min_string)


def add_tacklers(play,desc):
    para_dex = desc.find('(')
    pen_dex = desc.find('PENALTY')
    # Check for no potential tacklers
    if para_dex == -1:
        return(play)
    # Check if players in parentheses are penalized and not tacklers
    elif pen_dex != -1 and para_dex > pen_dex:
        return(play)
    capture_list = re.findall('\((.*?)\)',desc)
    t_list = [capture for capture in capture_list if capture.find('blocked') == -1]
    if len(t_list) > 0:
        t_string = t_list[0]
    else:
        return(play)
    tacklers = [tackler.strip() for tackler in t_string.split(';')]
    play[tackler1] = tacklers[0]
    if len(tacklers) >1:
        play[tackler2] = tacklers[1]
    return(play)


def add_fumble(play,poss,f_string,re_select,fumble_n):
    fum_keys = [fumbled_by, recover_team, recovered_by, forced_by]
    defense = [team for team in re_select.keys() if team != poss][0]
    if fumble_n > 1:
        for i in range(len(fum_keys)):
            fum_keys[i] = fum_keys[i] + str(fumble_n)
    # Muffs will happen before fumbles, so check for those first
    fumbler = re.findall("muffed by " + re_select[poss],f_string)
    if len(fumbler) == 0:
        fumbler = re.findall("fumbled* by " + re_select[poss],f_string)
    if len(fumbler) > 0:
        play[fum_keys[0]] = fumbler[0]
    recovery = re.findall("recovered by ([A-Z\d&']+) ",f_string)
    if len(recovery) > 0:
        play[fum_keys[1]] = recovery[0]
        recovered_by_name = re.findall('recovered by ' + recovery[0] + ' ' + re_select[recovery[0]],f_string)
        if len(recovered_by_name) > 0:
            play[fum_keys[2]] = recovered_by_name[0]
    forced = re.findall("fumble forced by " + re_select[defense],f_string)
    if len(forced) >0:
        play[fum_keys[3]] = forced[0]
    play[fumble_count] = fumble_n
    if fum_keys[1] in play.keys():
        play[fumble_poss] = play[fum_keys[1]]
    fum_return = max(f_string.find(' return'), f_string.find(' for'))
    if fum_return > -1:
        play = add_return(play,f_string,poss,re_select[defense])
    return(play)



def add_penalty(play,desc,re_select):
    # Consider only the text after 'PENALTY' and before first yard line mentioned
    pen_str = desc[desc.find('PENALTY'):]
    stop = re.search('[A-Z]+[0-9]+',pen_str)
    if stop:
        pen_str = pen_str[:stop.span()[0]]
    team = [tag for tag in re.findall(' ([A-Z]+)',pen_str) if tag in re_select.keys()]
    # Consider all possible penalties (potentially multiple for either team)
    for i in range(len(team)):
        # Create dictionary key (i.e. pen_team1) for nth penalty on the play
        team_key = pen_team + str(i+1)
        # Assign the value of that team's name abbr
        play[team_key] = team[i]
        # Isolate string info for just the nth penalty
        start_curr = re.search(team[i],pen_str).span()[1]
        try:
            stop_curr = pen_str[start_curr:].find(team[i+1]) + start_curr
        except:
            stop_curr = -1
        string_curr = pen_str[:stop_curr]
        # Extract the penalty name from string_curr testing 3 possible end markers
        ends = ('\(','[0-9]','decline')
        for j in range(len(ends)):
            try:
                penalty_name = re.findall(play[team_key] + ' (.*?) ' + ends[j],string_curr)[0]
                break
            except:
                if j+1 < len(ends):
                    continue
                else:
                    penalty_name = 'Not found'
        pen_key = penalty + str(i+1)
        play[pen_key] = penalty_name
        against_name = re.findall('\(' + re_select[team[i]] + '\)',string_curr)
        if len(against_name) > 0:
            against_key = against + str(i+1)
            play[against_key] = against_name[0]
        # If there are more penalties, remove the piece of the current penalty from the penalty string
        if stop_curr > -1:
            pen_str = pen_str[stop_curr:]
    penalty_yards = re.findall(' ([0-9]+) ',pen_str)
    if len(penalty_yards) > 0:
        play[pen_yards] = int(penalty_yards[0])
    return(play)



def add_return(play,r_string,poss,name_re):
    ret_patterns = (name_re + ' return', ' returned by ' + name_re, name_re + ' for')
    for pattern in ret_patterns:
        returner_name = re.findall(pattern,r_string)
        if len(returner_name) > 0:
            play[returner] = returner_name[0]
            break
    return_yards = re.findall(' ([0-9]+) yards',r_string)
    if len(return_yards)>0:
        play[ret_yards] = return_yards[0]
    return_yl = re.findall('([A-Z]+)([0-9]+)',r_string)
    if len(return_yl) > 0:
        play[ret_territory] = return_yl[0][0]
        return_spot_str = return_yl[0][1]
        if len(return_spot_str) > 2:
            return_spot_str = return_spot_str[-2:]
        return_spot = int(return_spot_str)
        if play[ret_territory] == poss:
            return_spot = return_spot*(-1)
        play[return_to] = return_spot
    return(play)
        
    


def run_parser(play,desc,name_re):
    play[play_type] = type_run
    rb = re.findall(name_re + ' rush',desc)
    if len(rb) > 0:
        play[rusher] = rb[0]
    if desc.find(' no gain') > -1:
        gain_loss = 0
    else:
        gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])
    if desc.find(" loss ") > -1:
        gain_loss = gain_loss*(-1)
    play[gn_ls] = gain_loss
    return(play)



def pass_parser(play,desc,poss,re_select):
    play[play_type] = type_pass
    defense = [team for team in re_select.keys() if team != poss][0]
    qb = re.findall(re_select[poss] + ' pass',desc)
    if len(qb) == 0:
        qb = re.findall(re_select[poss] + ' sacked',desc)
    if len(qb) > 0:
        play[passer] = qb[0]
    gain_loss = 0
    if desc.find(" incomplete") > -1:
        play[pass_result] = pass_incomplete
    if desc.find(" complete") > -1:
        try:
            gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])
        except:
            None
        play[pass_result] = pass_complete
    if desc.find(" sacked ") > -1:
        if re.search(' no gain', desc, re.IGNORECASE):
            gain_loss = 0
        else:
            gain_loss = int(re.findall(' ([0-9]+) ',desc)[0])*(-1)
        play[pass_result] = pass_sack
    play[gn_ls] = gain_loss
    # Determine intended WR and whether QB was intercepted or hurried
    intended_name = re.findall("complete to " + re_select[poss],desc)
    if len(intended_name) > 0:
        play[intended] = intended_name[0]
    intercepted = re.findall("intercepted by " + re_select[defense],desc)
    if len(intercepted) > 0:
        play[pass_result] = pass_interception
        play[intercepted_by] = intercepted[0]
        int_return = desc.find(' return')
        if int_return > -1:
            int_dex = re.search(' intercepted', desc)
            r_string = desc[int_dex.span()[1]:]
            play = add_return(play,r_string,poss,re_select[defense])
    hurried = re.findall("QB hurried by " + re_select[defense],desc)
    if len(hurried) > 0:
        play[hurried_by] = hurried[0]
    pbu = re.findall("broken up by " + re_select[defense],desc)
    if len(pbu) > 0:
        play[broken_up_by] = pbu[0]
    return(play)



def kop_parser(play,desc,poss,re_select):
    if desc.find('punt') > -1:
        ktype = 'punt'
        play[play_type] = type_punt
        k_keys = (punter,punt_yards,punt_to,punt_result)
    else:
        ktype = 'kickoff'
        play[play_type] = type_kickoff
        k_keys = (kicker,kick_yards,kick_to,kick_result)
    rec_team = [team for team in re_select.keys() if team != poss][0]
    # First consider the string segment containing kick info
    kick_yl = re.search('[A-Z]+[0-9]+',desc)
    if not kick_yl:
        kick_yl = re.search('[0-9]+ yardline',desc,re.IGNORECASE)
    if kick_yl:
        yl_string = kick_yl.group()
        yl_end = kick_yl.span()[1]
    else:
        yl_string = ''
        yl_end = -1
    k_string = desc[:yl_end]
    # Extract the kicker's name if it's there
    if k_string.find(ktype) > 0:
        kp = re.findall('^'+re_select[poss],k_string)
        if len(kp) > 0:
            play[k_keys[0]] = kp[0]
    yards = re.findall(ktype + ' ([0-9]+) yards',k_string)
    if len(yards) > 0:
        play[k_keys[1]] = int(yards[0])
    # Extract the yard line the ball was kicked to
    if len(yl_string) > 0:
        kick_land_str = re.findall('[0-9]+',yl_string)[0]
        if len(kick_land_str) > 2:
            kick_land_str = kick_land_str[-2:]
        kick_land = int(kick_land_str)
        if poss in yl_string:
            kick_land = kick_land*(-1)
        play[k_keys[2]] = kick_land
    # Determine whether a kickoff was on-side and who recovered it
    if ktype == 'kickoff' and re.search(' on-*side', desc, re.IGNORECASE):
        play[onside] = True
        recovery = re.findall("recovered by ([A-Z\d&']+) ",desc)
        if len(recovery) > 0:
            play[recover_team] = recovery[0]
            recovered_by_name = re.findall('recovered by ' + recovery[0] + ' ' + re_select[recovery[0]],desc)
            if len(recovered_by_name) > 0:
                play[recovered_by] = recovered_by_name[0]
    # Now consider the end of the string, either kick result or return
    if yl_end != -1:
        r_string = desc[yl_end:]
    else:
        r_string = desc
    if re.search('blocked', r_string, re.IGNORECASE):
        play[k_keys[3]] = punt_blocked
        blocker = re.findall('blocked by ' + re_select[rec_team], r_string)
        if len(blocker) > 0:
            play[blocked_by] = blocker[0]
        play = add_return(play,r_string,poss,re_select[rec_team])
    elif r_string.find(' return') > -1:
        play = add_return(play,r_string,poss,re_select[rec_team])
        play[k_keys[3]] = kp_return
    else:
        kp_result_dict = {'fair catch': kp_fair_catch, 'Touchback': kp_touchback,
                          'out-of-bounds': kp_out_of_bounds, ' out of bounds': kp_out_of_bounds}
        for kp_result in kp_result_dict.keys():
            if r_string.find(kp_result) > -1:
                play[k_keys[3]] = kp_result_dict[kp_result]
                break
    return(play)



def fg_parser(play,desc,poss,re_select):
    # Determine FG type and if string begins w/ kicker's name
    fg = desc.find('field goal')
    defense = [team for team in re_select.keys() if team != poss][0]
    if fg > -1: 
        play[play_type] = type_fg
        res_key = fg_result
        kick_dist = re.findall(' [0-9]{2} ',desc)
        try:
            play[fg_dist] = int(kick_dist[0])
        except:
            None
    else:
        play[play_type] = type_xp
        res_key = xp_result
        fg = desc.find('kick attempt')
    # Extract the placekicker's name if it's there
    if fg > 0:
        pk = re.findall('^'+re_select[poss],desc)
        if len(pk) > 0:
            play[placekicker] = pk[0]
    # Analyze substring after 'attempt'
    result_string = desc[desc.find('attempt'):]
    good = re.search('\w+ GOOD',result_string,re.IGNORECASE)
    missed = re.search(' MISSED',result_string,re.IGNORECASE)
    failed = re.search(' failed',result_string,re.IGNORECASE)
    blocked = re.search('blocked',result_string,re.IGNORECASE)
    if good:
        if re.search('NO',good.group(),re.IGNORECASE):
            play[res_key] = fg_no_good
        else:
            play[res_key] = fg_good
    elif blocked:
        play[res_key] = fg_blocked
        blocker = re.findall('blocked by ' + re_select[defense], result_string)
        if len(blocker) > 0:
            play[blocked_by] = blocker[0]
    elif missed or failed:
        play[res_key] = fg_no_good        
    fg_was_returned = max(result_string.find(' return'),result_string.find(' for'))
    if fg_was_returned > -1:
        play = add_return(play,result_string,poss,re_select[defense])
        if res_key not in play.keys() or play[res_key] != fg_blocked:
            play[res_key] = fg_return
    return(play)



def try_parser(play,desc,name_re):
    try_name = re.findall('^' + name_re,desc)
    if desc.find(' rush ') >-1:
        play[play_type] = type_run
        try:
            play[rusher] = try_name[0]
        except:
            None
    else:
        play[play_type] = type_pass
        try:
            play[passer] = try_name[0]
        except:
            None        
    if re.search(' failed',desc,re.IGNORECASE):
        play[two_point_attempt] = try_no_good
    else:
        play[two_point_attempt] = try_good
    return(play)
        


def timeout_parser(play,desc):
    play[play_type] = timeout
    team = re.findall('Timeout ([^,]+)', desc, re.IGNORECASE)
    try:
        play[taken_by] = team[0]
    except:
        None
    return(play)



def end_parser(desc, name_ref = None):
    end = dict()
    # Ensure that desc is not the drive start time stamp
    stamp = re.search("at [0-9]+:[0-9]{2}",desc,re.IGNORECASE)
    if stamp:
        return(end)
    # Extract the play and total yard counts    
    term_dict = {"play" : num_plays, "yard" : total_yards}
    for term in term_dict.keys():
        amount = re.findall("(\S*[0-9]+) " + term,desc)
        try:
            end[term_dict[term]] = int(amount[0])
        except:
            None
    time_elapsed = re.search("[0-9]+:[0-9]{2}",desc)
    if time_elapsed:
        end[time_of_possession] = time_elapsed.group()
        end[time_elapsed_sec] = time_conv(time_elapsed.group(),2)
    if name_ref:
        # Capture scores using presto update convention
        score_report = re.findall(name_ref[away_name] + ' ([\d]+), ' + name_ref[home_name] + ' ([\d]+)', desc)
        if not score_report:
            # Capture scores using sidearm update convention
            score_report = re.findall(name_ref[away_name] + ' ([\d]+)-([\d]+) ' + name_ref[home_name], desc)
        if score_report:
            end[away_score] = int(score_report[0][0])
            end[home_score] = int(score_report[0][1])
    if desc.find(' game') >-1:
        end[drive_end] = end_game
    elif desc.find(' half') >-1:
        end[drive_end] = end_half
    elif desc.find(' quarter') >-1:
        end[drive_end] = end_quarter
    elif desc.find('Change of possession') >-1:
        end[drive_end] = end_ot
    elif desc.find('Drive end unknown') > -1:
        end[drive_end] = end_unknown
    return(end)



def score_update(home_ball,points,play_state):
    if home_ball:
        play_state[home_score] += points
    else:
        play_state[away_score] += points
    play_state[score_diff] = play_state[home_score] - play_state[away_score]
    return(play_state)



def state_update(play,desc,play_state):
    # Determine whether the home team has possession in order to know which side to add/deduct from
    home_ball = play_state[possession] == play_state[home_abbr]
    # Update points based on play result
    # If the play was ruled a 'no play' or a score was nullified due to a penalty, don't update points
    if any((no_play in play.keys(), nullified in play.keys())):
        None
    # Otherwise...
    elif touchdown in play.keys():
        if fumble_poss in play.keys() and play[fumble_poss] != play_state[possession]:
            play_state.update(score_update(not home_ball,6,play_state))
            play_state[possession] = play[fumble_poss]
        elif fumble_poss in play.keys() and play[fumble_poss] == play_state[possession]:
            play_state.update(score_update(home_ball,6,play_state))
        elif any((pass_result in play.keys() and play[pass_result] == pass_interception,
                  fg_result in play.keys() and any((play[fg_result] == fg_blocked, play[fg_result] == fg_return)),
                  punt_result in play.keys() and any((play[punt_result] == punt_blocked, play[punt_result] == kp_return)),
                  kick_result in play.keys() and play[kick_result] == kp_return)):
            play_state.update(score_update(not home_ball,6,play_state))
            if home_ball:
                play_state[possession] = play_state[away_abbr]
            else:
                play_state[possession] = play_state[home_abbr]
        else:
            play_state.update(score_update(home_ball,6,play_state))
    elif xp_result in play.keys() and play[xp_result] == fg_good:
        play_state.update(score_update(home_ball,1,play_state))
    elif two_point_attempt in play.keys() and play[two_point_attempt] == try_good:
        play_state.update(score_update(home_ball,2,play_state))
    elif fg_result in play.keys() and play[fg_result] == fg_good:
        play_state.update(score_update(home_ball,3,play_state))
    if safety in play.keys() and play[safety]:
        play_state.update(score_update(not home_ball,2,play_state))
    if play_type in play.keys() and play[play_type] == timeout:
        if taken_by in play.keys():
            taken_by_team = play[taken_by].upper()
            if any((taken_by_team in play_state[home_name].upper(), taken_by_team in play_state[home_abbr])):
                play_state[home_tol] += -1
            elif any((taken_by_team in play_state[away_name].upper(), taken_by_team in play_state[away_abbr])):
                play_state[away_tol] += -1
    if play_state[quarter] < 5:
        clock = re.search('[0-9]+:[0-9]{2}', desc)
        if clock:
            time = clock.group()
            play_state[time_stamp] = time
            play_state[time_remaining] = time_conv(time,play_state[quarter])
    return(play_state)



class possession_tracker:
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
            possession_tracker.count += 1
        elif self.ball == self.away:
            self.ball = self.home
            possession_tracker.count += 1



def drive_end_finder(plays):
    end_dict = dict()
    last_play = plays[-1]
    # If a drive end has already been determined, return that
    if drive_end in plays[0].keys() and all((plays[0][drive_end], plays[0][drive_end] != end_unknown)):
        end_dict[drive_end] = plays[0][drive_end]
        if end_dict[drive_end] == end_half and last_play[quarter] in (1,3):
            end_dict[drive_end] = end_quarter
        return(end_dict)
    else:
        end = None
    # Determine whether a safety occurred during the drive
    was_safety = False
    for play in plays:
        if safety in play.keys():
            was_safety = True
            break
    time_ends = {game_end: end_game,half_end: end_half,quarter_end: end_quarter}
    common_key = set(time_ends.keys()) & set(last_play.keys())
    #Return None for quarter end drive summaries in which the drive hasn't ended
    if play_type not in last_play.keys():
        return({drive_end:None})
    if h_start in plays[0].keys() and last_play[play_type] == type_kickoff:
        return({drive_end:end_kick})         
    elif last_play[play_type] == type_kickoff:
        if q_start in plays[-2].keys():
            return({drive_end:None})
        elif was_safety:
            end = end_safety
        elif any((plays[-2][play_type] == type_xp, two_point_attempt in plays[-2].keys(), 
                  touchdown in plays[-2].keys())):
            end = end_td
        elif plays[-2][play_type] == type_fg:
            end = type_fg
        # If a re-kick took place, recur the function with the 2nd kick taken out
        elif plays[-2][play_type] == type_kickoff:
            end_dict = drive_end_finder(plays[:-1])
            return(end_dict)
        elif plays[-2][play_type] in (type_penalty, timeout):
            end_dict = drive_end_finder(plays[:-2] + [plays[-1]])
            return(end_dict)
    elif last_play[play_type] == type_punt:
        end = type_punt
    elif last_play[play_type] == type_fg:
        if last_play[fg_result] == fg_no_good:
            end = end_missed_fg
        elif last_play[quarter] in (1,3):
            end = type_fg
        elif last_play[quarter] == 2:
            end = end_half
        else:
            end = end_game
    elif pass_result in last_play.keys() and last_play[pass_result] == pass_interception:
        end = pass_interception
    elif all((fumble in last_play.keys(), 
              recover_team in last_play.keys())) and last_play[recover_team] != last_play[possession]:
        end = end_fumble
    elif gn_ls in last_play.keys() and last_play[down] == 4:
        if last_play[gn_ls] < last_play[distance]:
             end = end_downs
    elif last_play[play_type] == timeout:
        end = drive_end_finder(plays[:-1])
    elif len(common_key) > 0:
        end = time_ends[[x for x in common_key][0]]
        if end == end_half and last_play[quarter] in (1,3):
            end = end_quarter
    if drive_end in plays[0].keys() and all((plays[0][drive_end] == end_unknown, end == None, len(plays) > 1)):
        end_dict[drive_end] = end_unknown
    else:
        end_dict[drive_end] = end
    return(end_dict)
        
        
    
        
        


def toss_parser(drive0,name_dict):
    toss_dict = dict()
    # If a coin toss string exists, find it and extract relevant info
    toss_string = None
    for row in drive0:
        if row[-1].find(' toss') >-1:
            toss_string = row[-1]
            break
    if toss_string:
        winner = re.findall("([\w&'-]+) wins",toss_string)
        if len(winner) > 0:
            defer = toss_string.find(' defer')
            receive = toss_string.find(' receive')
            kick = toss_string.find(' kick')
            first_letters = (name_dict[home_abbr][0], name_dict[away_abbr][0])
            if winner[0] in name_dict[home_name] or winner[0] in name_dict[home_abbr]:
                toss_dict[won_toss] = name_dict[home_abbr]
            elif winner[0] in name_dict[away_name] or winner[0] in name_dict[away_abbr]:
                toss_dict[won_toss] = name_dict[away_abbr]
            elif first_letters[0] != first_letters[1] and winner[0][0] in first_letters:
                if winner[0][0] == name_dict[home_abbr][0]:
                    toss_dict[won_toss] = name_dict[home_abbr]
                else:
                    toss_dict[won_toss] = name_dict[away_abbr]
            else:
                a = set(winner[0]) & set(name_dict[home_name])
                b = set(winner[0]) & set(name_dict[away_name])
                if a:
                    toss_dict[won_toss] = name_dict[home_abbr]
                elif b:
                    toss_dict[won_toss] = name_dict[away_abbr]
            try:
                if toss_dict[won_toss] == name_dict[home_abbr]:
                    loser = name_dict[away_abbr]
                else:
                    loser = name_dict[home_abbr]
            except:
                toss_dict[won_toss] = 'Undetermined' 
            if defer >-1:
                toss_dict[winner_choice] = toss_defer
                if kick >-1 and any((re.search(name_dict[away_name],toss_string),re.search(name_dict[away_abbr],toss_string))):
                    toss_dict[loser_choice] = toss_kick
                    toss_dict[open_kick] = loser
                else:
                    toss_dict[loser_choice] = toss_receive
                    toss_dict[open_kick] = toss_dict[won_toss]
            elif receive >-1:
                toss_dict[winner_choice] = toss_receive
                toss_dict[open_kick] = loser
            else:
                toss_dict[winner_choice] = toss_kick
                toss_dict[open_kick] = toss_dict[won_toss]
    return(toss_dict)



def kicker_match(string,name_dict):
    kicker_name = re.findall('^(.*) kickoff', string)
    kick_team = None
    if len(kicker_name)>0:
        if name_dict[away_kicker] in kicker_name[0]:
            kick_team = name_dict[away_abbr]
        elif name_dict[home_kicker] in kicker_name[0]:
            kick_team = name_dict[home_abbr]
        else:
            k = {char for char in kicker_name[0] if char.isalpha()}
            a = k & set(name_dict[home_kicker])
            b = k & set(name_dict[away_kicker])
            if k == a:
                kick_team = name_dict[home_abbr]
            elif k == b:
                kick_team = name_dict[away_abbr]
    return(kick_team)
    
    
    
def possession_finder(drive,name_dict):
    poss = None
    # Try to find 'will receive' in drive strings
    for row in drive:
        receive = re.findall("([A-Z\d&']+) will receive",row[-1])
        if len(receive) > 0:
            if receive[0] == name_dict[home_abbr]:
                poss = name_dict[away_abbr]
            else:
                poss = name_dict[home_abbr]
            break
    # Try to find 'drive start' in drive strings
    if not poss:
        for row in drive:
            start_drive = re.findall('^(.*) drive start',row[-1])
            if len(start_drive) > 0:
                if name_dict[home_name].upper() in start_drive[0].upper() or start_drive[0].upper() in name_dict[home_name].upper():
                    poss = name_dict[home_abbr]
                elif name_dict[away_name].upper() in start_drive[0].upper() or start_drive[0].upper() in name_dict[away_name].upper():
                    poss = name_dict[away_abbr]
                break
    # Try to find 'ball' in drive strings
    if not poss:
        for row in drive:
            has_ball = re.findall("([A-Z\d&']+) ball",row[-1])
            if len(has_ball) > 0:
                poss = has_ball[0]
                break
    # Try to identify kicker name and match with kick team
    if not poss:
        kick_team = kicker_match(drive[-1][-1],name_dict)
        if kick_team:
            poss = kick_team
    return(poss)
        
    
        
def play_parser(string_list,poss,re_select,name_ref):
    if len(string_list) == 1:
        play = end_parser(string_list[0], name_ref)
        return(play)
    else:
        play = ddyl_parser(string_list[0],poss)
    desc = string_list[-1]
    # 2 point attempt
    if desc.find("rush attempt ") >-1 or desc.find("pass attempt ") >-1:
        play = try_parser(play,desc,re_select[poss])
    # Run
    elif desc.find(" rush ") >-1 or desc.startswith("rush "):
        play = run_parser(play,desc,re_select[poss])
    # Pass
    elif desc.find(" pass ") > -1 or desc.startswith('pass ') or desc.find(" sacked ") > -1:
        play = pass_parser(play,desc,poss,re_select)
    # Pre-snap penalty
    elif desc.startswith("PENALTY"):
        play[play_type] = type_penalty
        play = add_penalty(play,desc,re_select)
        return(play)
    # Timeout
    elif re.search('Timeout ', desc, re.IGNORECASE):
        play = timeout_parser(play,desc)
        return(play)
    # Kickoff / punt
    elif desc.find('kickoff') > -1 or desc.find('punt') > -1:
        play = kop_parser(play,desc,poss,re_select)
    # Extra point / field goal
    elif desc.find("field goal") > -1 or desc.find('kick attempt') > -1:
        play = fg_parser(play,desc,poss,re_select)
    # Kneel
    elif desc.startswith("Kneel "):
        play = run_parser(play,desc,re_select[poss])
        play[play_type] = type_kneel
        return(play)
    # Add tacklers
    play = add_tacklers(play,desc)
    # Add every fumble
    find_fumble = desc.find(' fumble')
    if find_fumble == -1:
        find_fumble = desc.find(' muffed')
    fumble_n = 0
    f_string = desc
    while find_fumble > -1:
        fumble_n += 1
        f_string = f_string[find_fumble:]
        play = add_fumble(play,poss,f_string,re_select,fumble_n)
        f_string = f_string[7:]
        find_fumble = f_string.find(' fumble')
        if fumble_poss in play.keys():
            poss = play[fumble_poss]
    # Add post-snap penalty
    if desc.find(' PENALTY ') > -1:
        play = add_penalty(play,desc,re_select)
    # Add result
    result_dict = {" TOUCHDOWN":touchdown, ' nullified': nullified, " NO PLAY": no_play, 
                   " 1ST DOWN": first_down, " safety": safety, " muffed": fumble,
                   " fumble": fumble, " game": game_end, " half": half_end,
                   ' quarter': quarter_end}
    for key in result_dict.keys():
        if re.search(key,desc,re.IGNORECASE):
            play[result_dict[key]] = True
    if play_type not in play.keys():
        play = end_parser(desc,name_ref)
    return(play)
    
    


def drive_parser(drive, game_state, re_select,quarter_tracker,drive_tracker,score_correct):
    plays = list()
    # Dictionary to store drive info...
    info = {key:game_state[key] for key in game_state.keys() if key != time_stamp}
    # ...stored as the '0' play of the drive
    plays.append(info)
    # Can check possession by passing in name_dict and parsing initial strings
    start = 0
    q = drive_dex('Start of ([1-9]).*quarter',drive)
    ds = drive_dex('drive start', drive)
    # Store names for access later
    name_ref = {key:game_state[key] for key in (home_name, away_name, home_abbr, away_abbr)}  
    # Determine whether the "drive" is the start of a quarter
    if drive_tracker == 0:
        info[q_start] = True
        # Set the quarter
        if quarter_tracker + 1 > 4:
            info[quarter] = 5
            info[drive_start] = '0:00'
        else:
            info[quarter] = quarter_tracker + 1
            # New quarter = start time of '15:00'
            info[drive_start] = '15:00'
        # Determine the start of plays to parse
        if quarter_tracker in (0,2):
            info[h_start] = True
            info[time_remaining] = time_conv(info[drive_start],info[quarter])
            game_state.update({quarter: info[quarter],
                   time_stamp: info[drive_start],
                   time_remaining: info[time_remaining]})
            ko = drive_dex('kickoff ', drive)
            if ko:
                play = play_parser(['Opening kickoff',drive[ko[0]][-1]], game_state[possession],re_select,name_ref)
            else:
                play = play_parser(['Opening kickoff',drive[-1][-1]], game_state[possession],re_select,name_ref)
            # Catch and fix regex pattern for naming protocol for either team
            if quarter_tracker == 0:
                names = name_check(play,name_keys)
                ko_keys = {kicker, tackler1, tackler2} & names.keys()
                ret_keys = {returner} & names.keys()
                if names:
                    play.update(names)
                    if ko_keys:
                        re_select[game_state[possession]] = get_name_format(names[list(ko_keys)[0]])
                    if ret_keys:
                        defense = [abbr for abbr in (game_state[home_abbr], game_state[away_abbr]) if abbr != game_state[possession]][0]
                        re_select[defense] = get_name_format(names[list(ret_keys)[0]])   
            if play_type not in play.keys():
                play[play_type] = type_kickoff
                play[drive_end] = open_kick
            play.update(game_state)
            plays.append(play)
            game_state = state_update(play,drive[-1][-1],game_state)
            if ko and -1 < ko[0] < len(drive)-1:
                for i in range(ko[0]+1,len(drive)):
                    play = play_parser(['',drive[i][-1]], game_state[possession],re_select,name_ref)
                    if play and play_type in play.keys():    
                        play.update(game_state)
                        plays.append(play)
                        game_state = state_update(play,drive[i][-1],game_state)
                    else:
                        info.update(play)
            return(plays)
        if q:
            start = q[0]+1
        if ds:
            start = ds[0]+1
    else:
        info[q_start] = False
        # Set drive start time
        if info[quarter] > 4:
            info[drive_start] = '0:00'
        else:
            info[drive_start] = game_state[time_stamp]
            for i in range(len(drive)):
                times = re.findall('[0-9]+:[0-9]{2}',drive[i][-1])
                if len(times) > 0:
                    info[drive_start] = times[0]
                    break
        # String after 'drive start' begins plays
        if ds:
            start = ds[0]+1  
        else:
            start = 1
    info[time_remaining] = time_conv(info[drive_start],info[quarter])
    game_state.update({quarter: info[quarter],
                       time_stamp: info[drive_start],
                       time_remaining: info[time_remaining],
                       home_tol: info[home_tol],
                       away_tol: info[away_tol]})                 
    while start < len(drive):
        play = play_parser(drive[start],game_state[possession],re_select,name_ref)
        name_check_tracker = [0,0]
        if all((quarter_tracker == 0, drive_tracker == 0, name_check_tracker == [0,0])):
            names = name_check(play, name_keys)
            if names:
                play.update(names)
                off_keys = {passer, rusher, intended, placekicker, punter, fumbled_by} & names.keys()
                def_keys = {returner, tackler1, tackler2, forced_by, hurried_by, broken_up_by, intercepted_by} & names.keys()
                if off_keys and name_check_tracker[0] == 0:
                    re_select[game_state[possession]] = get_name_format(names[list(off_keys)[0]])
                    name_check_tracker[0] += 1
                if def_keys and name_check_tracker[1] == 0:
                    defense = [abbr for abbr in (name_dict[home_abbr], name_dict[away_abbr]) if abbr != game_state[possession]][0]
                    re_select[defense] = get_name_format(names[list(def_keys)[0]])
                    name_check_tracker[1] += 1
        if play and play_type in play.keys():
            play.update(game_state)
            plays.append(play)
            game_state = state_update(play,drive[start][1],game_state)  
        elif all((play, home_score in play.keys(), score_correct)):
            if game_state[home_score] != play[home_score] or game_state[away_score] != play[away_score]:    
                game_state.update(play)
                print('Score correction made in {} @ {} (index) quarter {} drive {}'.format(game_state[away_name], 
                    game_state[home_name], quarter_tracker, drive_tracker))
            #if play_type in plays[-1].keys() and any((plays[-1][play_type] == type_xp, two_point_attempt in plays[-1].keys())):
                
        else:    
            info.update(play)
        start += 1
    return(plays)
    
    

def game_builder(quarters,name_dict,i_stop=-1,j_stop=-1,d_stop=-1,score_correct=True):
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
    # Process drives starting with opening kickoff        
    game = list()
    i = 0 # Quarter index
    o = 0 # Overtime index
    while i < len(quarters):
        current_quarter = quarters[i]
        if all((i == i_stop, j_stop == -1, d_stop == -1)):
            return({drive_list:game,state_dict:game_state})
        j = 0 # Drive index
        for curr_drive in current_quarter:
            if all((i == i_stop, j == j_stop, d_stop == -1)):
                return({drive_list:game,state_dict:game_state})
            try:
                # Reset timeouts and possession at the start of the 3rd quarter
                if (i,j) == (2,0):
                    game_state.update({home_tol: 3, away_tol: 3})
                    poss = possession_finder(curr_drive,name_dict)
                    # If no possessor is found, set 2nd half kick team opposite 1st
                    if not poss:
                        ball.set(toss_info[open_kick])
                        ball.flip()
                    else:
                        ball.set(poss) 
                # Check for unexpected combination of drives, and split if necessary
                all_drives = [curr_drive]
                ds = drive_dex('(.*) drive start', curr_drive)
                if ds:
                    next_ds = drive_dex('(.*) drive start', curr_drive[ds[0]+1:])
                    curr_poss_team = ds[1]
                    if next_ds:
                        all_drives[0] = curr_drive[:ds[0]+next_ds[0]+1]
                        next_poss_team = next_ds[1]
                        if all_drives[-1][-1][-1].find('Change of possession') == -1 and curr_poss_team != next_poss_team:
                                all_drives[-1].append(['Drive end unknown'])
                        all_drives.append(curr_drive[ds[0]+next_ds[0]+1:])
                        next_ds = drive_dex('(.*) drive start', all_drives[-1][1:])
                        curr_poss_team = next_poss_team
                        while next_ds:
                            trunc_drive = all_drives[-1]
                            next_dex = next_ds[0]
                            all_drives[-1] = trunc_drive[:next_dex+1]
                            next_poss_team = next_ds[1]
                            if all_drives[-1][-1][-1].find('Change of possession') == -1 and curr_poss_team != next_poss_team:
                                all_drives[-1].append(['Drive end unknown'])
                            all_drives.append(trunc_drive[next_dex+1:])
                            next_ds = drive_dex('(.*) drive start', all_drives[-1][1:])
                d = 0
                for drive in all_drives:        
                    if all((i == i_stop, j == j_stop, d == d_stop)):
                        return({drive_list:game,state_dict:game_state})
                    # Reset timeout and set possession at the start of each overtime period
                    if i > 3:
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
                        if d > 0:
                            j += 1
                        if j > 0 and j % 2 == 0:
                            o += 1
                            game_state.update({overtime: o})
                    # Run drive parser
                    ds = drive_dex('(.*) drive start', drive)
                    if ds and ds[1] not in name_dict[ball.get()]:
                        game_state[possession] = possession_finder(drive, name_dict)
                        if not game_state[possession]:
                            game_state[possession] = ball.get()
                        elif game_state[possession] != ball.get():
                            ball.flip()
                    else:
                        game_state[possession] = ball.get()
                    plays = drive_parser(drive,game_state,re_select,i,j,score_correct)
                    # Determine drive end and update info
                    info = plays[0]       
                    info.update(drive_end_finder(plays))
                    if j == len(current_quarter)-1 and not info[drive_end]:
                        info[drive_end] = end_quarter
                    if len(game) > 0:
                        last_drive = game[-1]
                    # Check for unexpected splitting of the drive tables (creating a drive with no plays), 
                    # except for Q3 and OT start. Combine if split.
                    if all((i not in (2,4), not info[q_start])) and play_type not in last_drive[-1].keys(): 
                        last_drive[0].update(info)
                        if len(plays) > 1:
                            game[-1] = last_drive + plays[1:]  
                    # If the drive is the start of 2nd or 4th quarter, merge it with the previous drive
                    # unless the last play of the previous quarter was a drive-ending play
                    elif info[q_start] and i in (1,3):
                        if not last_drive[0][drive_end] or last_drive[0][drive_end] == end_quarter:
                            # Update last drive info with q_start drive info
                            last_drive[0][drive_end] = info[drive_end]
                            for end_key in (num_plays, total_yards, time_elapsed_sec):
                                if end_key in info.keys():
                                    last_drive[0][end_key] = info[end_key]
                            # Append plays individually at the end of last drive
                            game[-1] = last_drive + plays[1:]
                            game[-1][0].update(drive_end_finder(game[-1]))
                        else:
                            game.append(plays)
                    # If the previous drive ended on a 'No Play' , if the current drive started on a down later than 1st, 
                    # or if the current drive starts with an XP, merge the current and previous drives
                    elif all((len(game) > 0, len(plays) > 1)) and any((no_play in last_drive[-1].keys(), 
                        plays[1][play_type] == type_xp, two_point_attempt in plays[1].keys(),
                        all((not last_drive[0][drive_end], down in plays[1].keys() and plays[1][down] > 1)))):
                        last_drive[0][drive_end] = info[drive_end]
                        for end_key in (num_plays, total_yards, time_elapsed_sec):
                            if end_key in info.keys():
                                if end_key in last_drive[0].keys():
                                    last_drive[0][end_key] += info[end_key]
                                else:
                                    last_drive[0][end_key] = info[end_key]
                        if time_elapsed_sec in last_drive[0].keys():
                            last_drive[0][time_of_possession] = sec_to_min(last_drive[0][time_elapsed_sec])
                        game[-1] = last_drive + plays[1:]
                        game[-1][0].update(drive_end_finder(game[-1]))
                    # If the opening half KO gets pushed to drive index 1, update the placekeeper KO play from
                    # the previous drive
                    elif (all((len(plays) > 1, len(game) > 0)) and play_type in last_drive[-1].keys()) and all((
                              last_drive[-1][play_type] == type_kickoff, plays[1][play_type] == type_kickoff)):
                        poss_holder = last_drive[-1][possession]
                        last_drive[-1].update(plays[1])
                        last_drive[-1][possession] = poss_holder
                    else:
                        game.append(plays)
                    # Determine whether possession object should stay or flip
                    last_play = plays[-1]
                    updated_info = game[-1][0]
                    # Don't flip possession on KO or Punt play when poss goes to kick team
                    if fumble in last_play.keys() and fumble_poss in last_play.keys():    
                        if last_play[fumble_poss] != ball.get():
                            ball.flip()
                        # But DO flip it if the possession team recovers but is still short of a conversion
                        elif updated_info[drive_end] == end_downs:
                            ball.flip()
                    elif onside in last_play.keys() and recover_team in last_play.keys():
                        if last_play[recover_team] != ball.get():
                            ball.flip()
                    # Flip possession if there is a turnover (TD) in the previous drive but the xp and/or ko is
                    # moved to the next drive
                    elif last_play[possession] != ball.get() and last_play[play_type] != type_kickoff:
                        ball.flip()
                    # Don't flip possession if the drive 'ended' with the last play of the quarter,
                    # on a 'no play', or if a drive end could not be identified (premature split of drive)
                    elif any((updated_info[drive_end] == end_quarter, no_play in plays[-1].keys(), 
                              not updated_info[drive_end])):
                        None
                    # Don't flip possession if an opening half kick correction was just made
                    elif play_type in game[-1][-1] and all((game[-1][-1][play_type] == type_kickoff,
                                                            game[-1][-1][possession] != ball.get(),
                                                            updated_info[drive_end] == end_kick)):
                        None
                    # Flip possession if the team who started with the ball also ended with it.
                    # Note: This means that if there was a turnover TD and the ball was subsequently kicked off,
                    # possession is not flipped.
                    elif last_play[possession] == ball.get():
                        ball.flip()
                    updated_info[poss_arrow] = ball.get()
                    d += 1
                j += 1
            except:
                print('Exception in {} (index) quarter {} drive {}'.format(name_dict[matchup],i,j))
                for row in quarters[i][j]:
                    print('\t',row)
                #raise
                print(traceback.format_exc())
                return({drive_list:game, state_dict:game_state, plays_list:plays})
        i += 1
    game_state.update(toss_info)
    return({drive_list:game,state_dict:game_state})
    


