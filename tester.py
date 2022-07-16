
from hudl_namespace import *
from pbp_parser import quarters, name_dict
from play_maker_hudl import game_builder
game_info = game_builder(quarters,name_dict)
game = game_info['game']
state = game_info['state']
