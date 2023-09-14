from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
import numpy as np
import ssl


# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 


def pot(headers, url, strainer = None):
    '''
    

    Parameters
    ----------
    headers : for urllib.request
    url : address of html you want parsed
    strainer : TYPE, optional
        BS strainer on hmtl tag to parse on part of the html. The default is None.

    Returns
    -------
    parsed html to be passed into pd.read_html()

    '''
    # Get decoded html from url
    request = Request(url,None,headers) #The assembled request
    response = urlopen(request, context=ctx)
    html = response.read().decode(errors='ignore') # The data u need
    # Parse html with BS
    # Strainer identifies part of html to parse for improved efficiency
    if strainer:
        return BeautifulSoup(html, "html.parser", parse_only=strainer)
    else:
        return(BeautifulSoup(html, "html.parser"))
    
    

def presto_parser(soup):
    '''
    

    Parameters
    ----------
    url : URL for presto-based html to be parsed

    Returns
    -------
    Dataframe with quarter and drive starts identified

    '''
    html = str(soup)
    df = pd.read_html(html)[0]
    df.columns = ['dd_str', 'play_str']
    df['top'] = np.where(df['dd_str'] == 'back to top',1,0)
    tops = list(df[df['top'] == 1].index)
    qtr_starts = [0,*[item+1 for item in tops[:-1]]]
    df['qtr_first_row'] = df.index.isin(qtr_starts)
    df['drive_first_row'] = df['qtr_first_row']
    df['drive_first_row'] = np.where((df['dd_str'] == df['play_str']) & 
                                     (df['play_str'].str.contains('at \d{2}:\d{2}')),True,df['drive_first_row'])
    df.drop(tops, axis = 0, inplace = True)
    df.drop('top', axis = 1, inplace = True)
    df.reset_index(drop = True, inplace = True)
    return df


def get_info_dict(box_soup, player_map, presto = False):
    if not presto:
        box = box_soup.find('tbody')
        names = [name.string for name in box.find_all(class_='hide-on-small-down')]
        abbrs = [abbr.string for abbr in box.find_all(class_='hide-on-medium')]
        info_dict = {'away_team': names[0], 'home_team': names[1], 'away_abbr': abbrs[0], 'home_abbr': abbrs[1]}
        game_info = box_soup.find(class_='text-center inline')
        keys = [key.string[:-1] for key in game_info.find_all('dt')][:-1]
        values = [value.string for value in game_info.find_all('dd')][:-1]
        info_dict.update(dict(zip(keys,values)))
    else:
        off_player_box = box_soup.find_all(class_='stats-fullbox clearfix')[-2]
        box_dfs = pd.read_html(str(off_player_box))
        names = box_dfs[0].iloc[0].tolist()
        box_indices = (1,3,7,9,11)
        abbrs = []
        for j in range(2):
            side_dfs = [box_dfs[i+j] for i in box_indices]
            side_players = pd.concat([side_df.iloc[:,0] for side_df in side_dfs]).drop_duplicates()
            side_abbr = side_players.map(player_map).dropna().unique().tolist()
            assert len(side_abbr) == 1, f'Error assigning abbreviation for {names[j]}'
            abbrs.extend(side_abbr)
        info_dict = {'away_team': names[0], 'home_team': names[1], 'away_abbr': abbrs[0], 'home_abbr': abbrs[1]}
        info_box = box_soup.find(class_='stats-fullbox summary other-info clearfix')
        info_strings = list(info_box.stripped_strings)
        info_strings = info_strings[info_strings.index('Location:'):info_strings.index('Referee:')]
        keys = [string.replace(':','') for string in info_strings if string.find(':') > -1]
        values = [string for string in info_strings if string.find(':') == -1]
        info_dict.update(dict(zip(keys,values)))
    return info_dict

def get_roster(roster_soup, presto = False):
    if not presto:
        roster = [table for table in pd.read_html(str(roster_soup)) if len(table) > 0][0]

        
