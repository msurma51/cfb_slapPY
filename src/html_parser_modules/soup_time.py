from urllib.request import Request, urlopen
from bs4 import BeautifulSoup, SoupStrainer
import pandas as pd
import numpy as np
import ssl

import os, sys
sys.path.append(os.path.split(os.getcwd())[0])
from play_maker_modules.play_maker_funcs import name_extract
from selenium_edge import get_d3_teams

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
    
def get_schedule_d3(schedule_url):
    soup = pot(headers, schedule_url)
    schedule = pd.read_html(str(soup.find('table')))[0][1:]
    schedule = schedule.rename(columns = {0: 'date', 1: 'opponent', 2: 'time'})
    schedule[['month', 'day']] = schedule.date.str.split('/', expand = True)
    split_url = schedule_url.split(sep = '/')
    team_name, season = split_url[4], int(split_url[5])
    for time_unit in ['month', 'day']:
        schedule[time_unit] = schedule[time_unit].mask(
            schedule[time_unit].str.len() < 2, '0' + schedule[time_unit]  
        )
    schedule['year'] = np.where(schedule.month.astype(int) >= 8, season, season + 1).astype(str)
    schedule['date'] = schedule[['year', 'month', 'day']].agg('-'.join, axis = 1)
    schedule['team_name'] = team_name
    schedule['opp_team_name'] = schedule.opponent.str.split(' ', expand = True).iloc[:, 1].str.strip()
    schedule['home'] = schedule.opponent.str.contains('vs.').astype(int)
    schedule['is_d3_opp'] = schedule.opponent.str.contains('•', regex = False).astype(int)
    schedule['is_conf_opp'] = schedule.opponent.str.contains('*', regex = False).astype(int)
    return schedule[['date', 'time', 'team_name', 'opp_team_name', 'home', 'is_d3_opp', 'is_conf_opp']]
    
    
def get_d3_team_info_all(url):
    teams = get_d3_teams(url)
    
    
def get_roster(roster_soup, sidearm = True):
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

def get_split_fields_dict(s, field_names, sep = ' ', dtype = None, rename_indices = None):
    df = s.str.split(sep, expand = True)
    if not rename_indices:
        df.columns = field_names
    else:
        df = df.rename(columns = dict(zip(rename_indices, field_names)))
    if dtype:
        df = df.astype(dtype)
    return df.to_dict()
    
def get_team_stats(team_soup, sidearm = True):
    from namespaces.box_score import (
        total_first_downs, passing_first_downs, rushing_first_downs, penalty_first_downs, 
        third_down_attempts, third_down_conversions, third_down_efficiency, 
        fourth_down_attempts, fourth_down_conversions, fourth_down_efficiency,
        total_offense, offense_plays, offense_yards_per_play, 
        passing_yards, pass_attempts, pass_completions, passing_yards_per_attempt, 
        passing_yards_per_completion, pass_tds, passes_intercepted, 
        sacks_allowed, sacks_allowed_yards, 
        rushing_yards, rush_attempts, rushing_yards_per_attempt, rush_tds,
        rushing_yards_gained, rushing_yards_lost,
        punt_attempts, punting_yards, punting_yards_per_attempt,
        punts_inside_20, punts_50_plus, punt_touchbacks, punt_fair_catches,
        kickoff_attempts, kickoff_yards, kickoff_yards_per_attempt, kickoff_touchbacks,
        total_return_yards, punt_returns, punt_return_yards, punt_return_tds, punt_return_avg,
        kickoff_returns, kickoff_return_yards, kickoff_return_tds, kickoff_return_avg,
        interception_returns, interception_return_yards, interception_return_tds,
        fumble_recoveries, fumble_return_yards, fumble_return_tds,
        penalties, penalty_yards, fumbles, fumbles_lost, sacks, sack_yards,
        interceptions, interception_yards, time_of_possession,
        misc_yards, red_zone_chances, red_zone_scores, 
        xp_attempts, xp_made, two_point_attempts, two_point_made, fg_attempts, fg_made,
    )
    stat_dict = dict()
    if sidearm:
        team_df = pd.read_html(str(team_soup))[0]
        for col in team_df.columns:
            team_df[col] = team_df[col].str.replace(' +', ' ', regex = True)
            team_df[col] = team_df[col].str.replace('-+', '-', regex = True)
        team_df['is_title_row'] = (
            team_df[team_df.columns.values[0]] == team_df[team_df.columns.values[1]]
        ).astype(int)
        team_df = team_df[team_df.is_title_row == 0][team_df.columns.values[:-1]]
        team_df = team_df.set_index('Statistic')
        int_fields = [
            total_first_downs, rushing_first_downs, passing_first_downs, penalty_first_downs,
            rushing_yards, rush_attempts, rush_tds, rushing_yards_gained, rushing_yards_lost,
            passing_yards, pass_tds, total_offense, offense_plays, 
            punts_inside_20, punts_50_plus, punt_touchbacks, punt_fair_catches,
            kickoff_touchbacks, misc_yards,
        ]
        int_indices = [0,1,2,3,4,5,7,8,9,10,14,15,16,22,23,24,25,28,35,]
        int_df = team_df.iloc[int_indices].astype(int)
        int_df.index = int_fields
        stat_dict.update(int_df.to_dict(orient = 'index'))
        float_fields = [
            rushing_yards_per_attempt, passing_yards_per_attempt, passing_yards_per_completion,
            offense_yards_per_play, punting_yards_per_attempt, kickoff_yards_per_attempt,
            punt_return_avg, kickoff_return_avg,
        ]
        float_indices = [6, 12, 13, 17, 21, 27, 30, 32]
        float_df = team_df.iloc[float_indices].astype(float)
        float_df.index = float_fields
        stat_dict.update(float_df.to_dict(orient = 'index'))
        dash_split_lists = [
            [pass_completions, pass_attempts, passes_intercepted,],
            [fumbles, fumbles_lost,],
            [penalties, penalty_yards,],
            [punt_attempts, punting_yards],
            [kickoff_attempts, kickoff_yards,],
            [punt_returns, punt_return_yards, punt_return_tds,],
            [kickoff_returns, kickoff_return_yards, kickoff_return_tds,],
            [interceptions, interception_return_yards, interception_return_tds,],
            [fumble_recoveries, fumble_return_yards, fumble_return_tds],
            [red_zone_scores, red_zone_chances,],
            [sacks, sack_yards,],
            [xp_made, xp_attempts],
            [two_point_made, two_point_attempts,],
            [fg_made, fg_attempts,],
        ]
        dash_split_indices = [11, 18, 19, 20, 26, 29, 31, 33, 34, 39, 40, 41, 42, 43,]
        for stat_list, dex in zip(dash_split_lists, dash_split_indices):
            stat_dict.update(
                get_split_fields_dict(
                    team_df.iloc[dex],
                    field_names = stat_list,
                    sep = '-',
                    dtype = int,
                )   
            )
        conv_field_lists = [
            [third_down_conversions, third_down_attempts,],
            [fourth_down_conversions, fourth_down_attempts],
        ]
        conv_field_indices = [37, 38]
        for conv_field_list, dex in zip(conv_field_lists,conv_field_indices):
            stat_dict.update(
                get_split_fields_dict(
                    team_df.iloc[dex],
                    field_names = conv_field_list,
                    sep = ' of ',
                    dtype = int,
                )   
            )
        stat_dict[time_of_possession] = team_df.iloc[36].to_dict()
    else: # Presto
        team_box = team_soup.find_all(class_='table')[3]
        team_df = pd.read_html(str(team_box))[0].set_index('Statistics')
        for col in team_df.columns:
            team_df[col] = team_df[col].str.replace(' +', ' ', regex = True)
            
        int_fields = [
            total_first_downs, total_offense, passing_yards, rushing_yards,
            total_return_yards, 
        ]
        int_indices = [0,4,6,8,12]
        int_df = team_df.iloc[int_indices]
        int_df.index = int_fields
        stat_dict.update(int_df.to_dict(orient = 'index'))

        stat_dict[punting_yards_per_attempt] = team_df.iloc[11].to_dict()
        # Split first downs by attempt type and map
        stat_dict.update(
            get_split_fields_dict(
                team_df.iloc[1],
                field_names = [rushing_first_downs, passing_first_downs, penalty_first_downs,],
                sep = ' ',
            )   
        )
        third_down_fields = [third_down_efficiency, third_down_conversions, third_down_attempts,]
        fourth_down_fields = [fourth_down_efficiency, fourth_down_conversions, fourth_down_attempts,]
        for i, cd_fields in enumerate((third_down_fields, fourth_down_fields)):
            cd_df = team_df.iloc[i+2].str.split(' ', expand = True)[[0,1,3,]]
            cd_df[0] = cd_df[0].str.replace('\%', '', regex = True).astype(int) / 100
            cd_df[1] = cd_df[1].str.replace('\(', '', regex = True)
            cd_df[3] = cd_df[3].str.replace('\)', '', regex = True)
            cd_df.columns = cd_fields
            stat_dict.update(cd_df.to_dict())
        stat_dict.update(
            get_split_fields_dict(
                team_df.iloc[5],
                field_names = [total_offense, offense_yards_per_play,],
                sep = ' ',
            )   
        )
        stat_dict[passing_yards] = team_df.iloc[6].to_dict()
        pass_df = team_df.iloc[7].str.split(' ', expand = True)
        stat_dict.update(
            get_split_fields_dict(
                pass_df[0],
                field_names = [pass_completions, pass_attempts,],
                sep = '-',
            )  
        )
        stat_dict[passing_yards_per_attempt] = pass_df[1].to_dict()
        stat_dict.update(
            get_split_fields_dict(
                pass_df[2],
                field_names = [sacks_allowed, sacks_allowed_yards,],
                sep = '-',
            )  
        )
        stat_dict[passes_intercepted] = pass_df[3].to_dict()
        stat_dict[rushing_yards] = team_df.iloc[8].to_dict()
        stat_dict.update(
            get_split_fields_dict(
                team_df.iloc[9],
                field_names = [rush_attempts, rushing_yards_per_attempt],
                sep = ' ',
            )  
        )
        stat_dict.update(
            get_split_fields_dict(
                team_df.iloc[10],
                field_names = [punt_attempts, punting_yards],
                sep = '-',
            )  
        )
        stat_dict[punting_yards_per_attempt] = team_df.iloc[11].to_dict()
        stat_dict[total_return_yards] = team_df.iloc[12].to_dict()
        ret_df = team_df.iloc[13].str.split(' ', expand = True)
        ret_lists = [
            [punt_returns, punt_return_yards,],
            [kickoff_returns, kickoff_return_yards,],
            [interception_returns, interception_return_yards,],
        ]
        for i, ret_list in enumerate(ret_lists):
            stat_dict.update(
                get_split_fields_dict(
                    ret_df[i],
                    field_names = ret_list,
                    sep = '-',
                )  
            )
        pfd_lists = [
            [penalties, penalty_yards,],
            [fumbles, fumbles_lost,],
            [sacks, sack_yards,],
            [interceptions, interception_yards],
        ]
        for j, pfd_list in enumerate(pfd_lists):
            stat_dict.update(
                get_split_fields_dict(
                    team_df.iloc[j+14],
                    field_names = pfd_list,
                    sep = '-',
                )  
            )
        # Convert to appropriate data types using pandas dataframe
        float_fields = [
            third_down_efficiency, fourth_down_efficiency, offense_yards_per_play,
            passing_yards_per_attempt, rushing_yards_per_attempt, punting_yards_per_attempt,
        ]
        int_fields = [field for field in stat_dict.keys() if field not in float_fields]
        df = pd.DataFrame(stat_dict)
        df[float_fields] = df[float_fields].astype(float)
        df[int_fields] = df[int_fields].astype(int)
        stat_dict = df.to_dict()
        stat_dict[time_of_possession] = team_df.iloc[-1].to_dict()
    return stat_dict
        
def get_player_stats(player_soup, sidearm = True):
    stat_dict = dict()
    if sidearm:
        stat_tables = pd.read_html(str(player_soup))
        pass_dfs = stat_tables[:2]
    return stat_dict
        
        
        
        
        
    
    

        
        
        
        
        
        
        
        
        
        
        
        
