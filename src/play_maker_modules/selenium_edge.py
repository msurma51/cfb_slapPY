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

def test_edge_session():
    service = EdgeService(executable_path=EdgeChromiumDriverManager().install())

    driver = webdriver.Edge(service=service)

    driver.quit()
    
def get_buttons(driver):
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    tab_names = [button.text for button in buttons]
    return buttons, tab_names
    
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
    
    
    
    


