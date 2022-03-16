from game_spider import box_score_links
from pbp_parser_func import *
from play_maker import *
games = list()
for url in box_score_links:
    quarters,name_dict = pbp_parser(url)
    game_info = game_builder(quarters,name_dict)
    games.append(game_info)
    state = game_info[1]
    print(state['away_abbr'],'@',state['home_abbr'],'parsed successfully')


