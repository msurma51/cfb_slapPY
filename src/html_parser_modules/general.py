from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
import numpy as np
import ssl

import os, sys
sys.path.append(os.path.split(os.getcwd())[0])
from play_maker_modules.play_maker_funcs import name_extract

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
    
    

def presto_parser(pbp_soup):
    '''
    

    Parameters
    ----------
    pbp_soup : BeautifulSoup object containing pbp info in PrestoSports style

    Returns
    -------
    Dataframe containing gamestate and play text with quarter and drive starts identified

    '''
    html = str(pbp_soup)
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


def get_game_summary(box_soup, sidearm = True):
    if sidearm:
        # Get generic boxscore table and convert to DataFrame
        box_table = box_soup.table
        table_body = box_table.tbody
        box_df = pd.read_html(str(box_table))[0]
        # Clean df
        box_df = box_df.drop(columns = box_df.columns.values[0])
        box_df = box_df.rename(columns = {col: col.split(' ')[0] for col in box_df.columns.values})
        # Get team names and abbreviations and add to df
        box_df['team_abbr'] = [tag.string for tag in table_body.find_all(class_ = 'hide-on-medium')[:2]]
        box_df['team_name'] =  [tag.string for tag in table_body.find_all(class_ = 'hide-on-small-down')[:2]]
        # Get generic game information (date, site, weather, attendance...)
        info_tag = box_soup.header.div.contents[-2]
        info_strings = list(info_tag.stripped_strings)
    else: # Presto
        # Get generic boxscore table and convert to DataFrame    
        tables = box_soup.find_all(class_='table')
        box = tables[1]
        box_df = pd.read_html(str(box))[0].iloc[:2]
        # Clean df
        team_names = box_df['Scoring'].str.extract('(.*) \(\d').squeeze()
        box_df['team_name'] = team_names.str.strip() # Presto boxscores don't include team abbreviation
        box_df = box_df.drop(columns = box_df.columns.values[0])
        box_df = box_df.rename(columns = {'Final': 'F'})
        # Get generic game information (date, site, weather, attendance...)
        info_strings = list(tables[-1].stripped_strings)
        info_strings = info_strings[info_strings.index('Location:'):]
        
    # Convert numeric game info values to integers
    game_info = [int(string) if string.isdigit() else string for string in info_strings]
    # Create game info dictionary by mapping info keys to values (which alternate in list)
    game_dict = {game_info[i]: game_info[i+1] for i in np.arange(0,len(game_info),2)}
    # Convert game scores to integers
    score_cols = [col for col in box_df.columns if col.isdigit()]
    score_cols.append('F')
    box_df[score_cols] = box_df[score_cols].astype(int)
    # Create 'home' binary and identify each row as  'away' and 'home' respectively
    box_df.index.name = 'home'
    box_df['index'] = ['away', 'home']
    box_df = box_df.reset_index().set_index('index')
    # Update game dictionary with subdictionaries containing info and box score unique to each team
    game_dict.update(box_df.to_dict(orient = 'index'))

    return game_dict

def get_roster(roster_soup, presto = False):
    if not presto:
        roster = [table for table in pd.read_html(str(roster_soup)) if len(table) > 0][0]
        split_cols = [col for col in roster.columns if '/' in col]
        for col in split_cols:
            split_df = roster[col].str.split(pat = ' / ', expand = True).apply(lambda x: x.str.strip())
            split_df.columns = [colname.strip() for colname in col.split(sep = '/')]
            roster = pd.concat((roster, split_df), axis = 1).drop(split_cols, axis = 1)
    else:
        roster_raw = pd.read_html(str(roster_soup))[0]
        full_name = roster_raw.iloc[:,2].str.replace('  ', ' ', regex = True).rename('Name')
        roster = roster_raw.iloc[:,3:]
        roster.columns = roster_raw.columns.values[2:-1]
        split_cols = [col for col in roster.columns if '/' in col]
        roster = roster.apply(lambda x: x.str.replace(x.name + ': ', '', regex = True))
        for col in split_cols:
            split_df = roster[col].str.split(pat = ' / ', expand = True).apply(lambda x: x.str.strip())
            split_df.columns = [colname.strip() for colname in col.split(sep = '/')]
            roster = pd.concat((roster, split_df), axis = 1).drop(split_cols, axis = 1)
        schools = pd.DataFrame()
        if roster['High School'].str.contains('\(').any():
            schools = roster['High School'].str.split(pat = ' \(', expand = True)
            schools.columns = ['high_school', 'prev_school']
            schools['prev_school'] = schools.prev_school.str.replace('\)','', regex = True)
            if schools.prev_school.str.contains(',').any():
                prev_schools = schools.prev_school.str.split(pat = ',', expand = True)
                prev_schools.columns = (['prev_school'] + 
                                        [f'prev_school{i}' for i in range(2,len(prev_schools.columns)+1)])
                schools = pd.concat((schools.iloc[:,0],prev_schools), axis = 1)
        roster = pd.concat((roster_raw.iloc[:,0], full_name, 
                            roster.iloc[:,:-1], schools), axis = 1).fillna('')
        roster.columns = roster.columns.str.title()
    col_map = {'#': 'No.', 'Name': 'Full_Name', 'Full Name': 'Full_Name', 
               'Cl.': 'Yr.', 'High School': 'High_School'}    
    roster = roster.rename(columns = col_map)
    roster['Yr.'] = roster['Yr.'].replace('FY', 'Fr.')
    roster_cols = ['No.', 'Full_Name', 'Yr.', 'Pos.', 'Ht.', 'Wt.', 'Hometown', 'High_School']
    return roster[roster_cols]
        
        
        
        
        
        
        
        
        
        
        
        
