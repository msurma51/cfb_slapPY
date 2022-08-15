from bs4 import BeautifulSoup   
from hudl_namespace import *
url = input('Enter -')
try:
    from pbp_parser_func import pbp_parser
    quarters, name_dict = pbp_parser(url)
except:
    from taster_func import taster
    quarters, name_dict = taster(url)  
from play_maker_hudl import *
'''
game_info = game_builder(quarters,name_dict)
game = game_info['game']
state = game_info['state']
if 'plays' in game_info.keys():
    plays = game_info['plays']
    '''