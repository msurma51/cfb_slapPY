import json
from namespace_og import *
from game_spider import url, box_score_links
from pbp_parser_func import *
from play_maker import *
games = {'schedule_link' : url}
for link in box_score_links:
    quarters,name_dict = pbp_parser(link)
    game_info = game_builder(quarters,name_dict)
    state = game_info[state_dict]
    game_key = state[away_abbr]+' @ '+state[home_abbr]
    games[game_key] = game_info
    print(game_key,'parsed successfully')
with open('lycoming_test.json', 'w') as outfile:
    json.dump(games,outfile)
    