# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 22:42:23 2024

@author: surma
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import re

import os, sys
sys.path.append(os.path.split(os.getcwd())[0])


def test_edge_session():
    service = EdgeService(executable_path=EdgeChromiumDriverManager().install())

    driver = webdriver.Edge(service=service)

    driver.quit()
    
def get_url_edge_driver(url):
    driver = webdriver.Edge(service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
    driver.implicitly_wait(10)
    driver.get(url)
    return driver
    
def get_buttons(driver):
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    tab_names = [button.text for button in buttons]
    return buttons, tab_names

url = 'https://d3football.com/teams/index'
def get_teams_d3(url):
    from namespaces.teams import (
        team_name, nickname, city, state, conference, region, division, surface, enrollment, d3_url,
    )
    
    driver = get_url_edge_driver(url)
    
    table_tag = driver.find_element(By.CLASS_NAME, 'teaminfo')
    table = pd.read_html(table_tag.get_attribute('innerHTML'))[0]
    table.columns = table.columns.str.lower()
    table = table.rename(columns = {'school': 'team_name'})
    table[[city, state]] = table.location.str.split(', ', expand = True)
    row_tags = table_tag.find_elements(By.TAG_NAME, 'tr')
    team_links = [tag.find_element(By.TAG_NAME, 'a').get_attribute('href') for tag in row_tags[1:]]
    table[d3_url] = team_links
    table[division] = 3
    driver.quit()
    return table[
        [team_name, nickname, city, state, conference, region, division, surface, enrollment, d3_url,]
    ]

def get_team_info_d3(team_url):
    driver = get_url_edge_driver(team_url)
    past_year_tag = driver.find_element(By.CLASS_NAME, 'past-records-wrapper')
    past_years = pd.read_html(past_year_tag.get_attribute('innerHTML'))[0]
    past_years.columns = past_years.columns.str.lower()
    row_tags = past_year_tag.find_elements(By.TAG_NAME, 'tr')
    team_links = [tag.find_element(By.TAG_NAME, 'a').get_attribute('href') for tag in row_tags[1:]]
    past_years['schedule_url'] = team_links
    info_tag = driver.find_element(By.CLASS_NAME, 'info')
    info_list = []
    for class_name in ('label', 'value'):
        tags = info_tag.find_elements(By.CLASS_NAME, class_name)
        info_list.append([tag.text for tag in tags])
    info = pd.Series(
        info_list[1], 
        index = [label[:-1].lower() for label in info_list[0]]
    )
    info['team_name'] = team_url.split(sep = '/')[4]
    info['enrollment'] = int(info.enrollment.replace(',',''))
    info['coach_name']= re.search('(.*) \(', info.coach).group(1)
    info['coach_alma_mater']= re.search('\((.*)\)', info.coach).group(1)
    info['city'] = info.location.split(sep = ', ')[0]
    info['state'] = info.location.split(sep = ', ')[1]
    colors = info.colors.split(sep = ', ')
    info['stadium_name']= re.search('(.*) \(', info.stadium).group(1)
    info['stadium_capacity']= int(re.search('\((.*)\)', info.stadium).group(1).replace(',',''))
    for i, color in enumerate(colors):
        info['color_' + str(i+1)] = color
    info_index = ['team_name', 'coach_name', 'coach_alma_mater', 'conference', 'enrollment', 
                  'city', 'state', 'stadium_name', 'stadium_capacity', 'surface']
    info_index.extend([dex for dex in info.index if dex.startswith('color_')])
    try:
        link_row_tag = info_tag.find_elements(By.CLASS_NAME, 'row.clearfix')[-1]
        link_tag = link_row_tag.find_element(By.TAG_NAME, 'a')
        info['official_url'] = link_tag.get_attribute('href')
        info_index.append('official_url')
    except Exception as e:
        print('No official url found;', e)
    driver.quit()
    return past_years, info[info_index]
        

        
def selenium_soup(url):    
    driver = webdriver.Edge(service=EdgeService(executable_path=EdgeChromiumDriverManager().install()))
    driver.implicitly_wait(10)
    driver.maximize_window()
    
    driver.get(url)
    
    tab_names = []
    while 'Play-By-Play' not in tab_names:
        buttons, tab_names = get_buttons(driver)
    pbp_button = buttons[tab_names.index('Play-By-Play')]
    pbp_button.click()
    
    all_qtrs = ['1st', '2nd', '3rd', '4th', 'OT']
    while all_qtrs[0] not in tab_names:
        buttons, tab_names = get_buttons(driver)
    qtr_tabs = [tab for tab in tab_names if tab in all_qtrs]
    html_list = []
    for i, qtr in enumerate(qtr_tabs):
        buttons, tab_names = get_buttons(driver)
        qtr_tag = None
        while not qtr_tag:
            try:
                qtr_tag = driver.find_element(By.ID, qtr)
            except:
                continue
        html_list.append('<section>' + qtr_tag.get_attribute('innerHTML') + '</section>')
        if qtr != qtr_tabs[-1]:
            while qtr not in tab_names:
                buttons, tab_names = get_buttons(driver)
            next_qtr_button = buttons[tab_names.index(qtr_tabs[i+1])]
            next_qtr_button.click()
    html = '<section></section>' + ''.join(html_list)
    return BeautifulSoup(html, "html.parser")
        
url = 'https://mgoblue.com/sports/football/stats/2023/bowling-green/boxscore/25649'
    
    
    
    


