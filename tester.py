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
game_info = game_builder(quarters,name_dict)
'''
curr_drive = quarters[4][4]
all_drives = [curr_drive]
ds = drive_dex('drive start', curr_drive)
try:    
    if ds:
        next_ds = drive_dex('drive start', curr_drive[ds[0]+1:])
        if next_ds:
            all_drives[0] = curr_drive[:ds[0]+next_ds[0]+1]
            all_drives.append(curr_drive[ds[0]+next_ds[0]+1:])
            next_ds = drive_dex('drive start', all_drives[-1][1:])
            while next_ds:
                trunc_drive = all_drives[-1]
                next_dex = next_ds[0]
                all_drives[-1] = trunc_drive[:next_dex+1]
                if all_drives[-1][-1][-1].find('Change of possession') == -1:
                    all_drives[-1].append(['Drive end unknown'])
                all_drives.append(trunc_drive[next_dex+1:])
                next_ds = drive_dex('drive start', all_drives[-1][1:])
except:
    for drive in all_drives:
        print(drive)

game_info = game_builder(quarters,name_dict)
'''
re_select = dict()
re_select[name_dict[home_abbr]] = get_name_format(name_dict[home_kicker])
re_select[name_dict[away_abbr]] = get_name_format(name_dict[away_kicker])
game = game_info['game']
game_state = game_info['state']

