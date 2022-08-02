
from hudl_namespace import *
from taster_new import quarters, name_dict
from play_maker_new import *
game_info = game_builder(quarters,name_dict)
game = game_info['game']
state = game_info['state']
game_start = {home_score: 0, away_score: 0, score_diff: 0, home_tol: 3,
                  away_tol: 3, quarter: 1, time_stamp: '15:00',
                  time_remaining: 1800}
re_select = dict()
re_select[name_dict[home_abbr]] = get_name_format(name_dict[home_kicker])
re_select[name_dict[away_abbr]] = get_name_format(name_dict[away_kicker])
#d0 = quarters[0][0]
#state.update(game_start)
#plays = drive_parser(d0,state,re_select,0,0)