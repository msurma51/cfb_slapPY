# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 12:39:45 2024

@author: surma
"""

import os, sys
sys.path.append(os.path.split(os.getcwd())[0])

from namespaces.teams import (
    team_id, team_name, nickname, city, state, conference, region, division, 
    official_url, d3_url, stadium_name, stadium_capacity, surface, enrollment,
    color, coach_name, coach_alma_mater,
)

tables = {
    'teams':  {
        team_id: 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        team_name: 'VARCHAR (100) NOT NULL',
        nickname: 'VARCHAR (50)',
        city: 'VARCHAR (50)',
        state: 'VARCHAR (2)',
        conference: 'VARCHAR (50)',
        region: 'INTEGER',
        division: 'INTEGER NOT NULL',
        official_url: 'VARCHAR (250)',
        d3_url: 'VARCHAR (250)',
        stadium_name: 'VARCHAR (100)',
        stadium_capacity: 'INTEGER',
        surface: 'VARCHAR (50)',
        enrollment: 'INTEGER',
        color + '_1': 'VARCHAR (50)',
        color + '_2': 'VARCHAR (50)',
        color + '_3': 'VARCHAR (50)',
        coach_name: 'VARCHAR (100)', 
        coach_alma_mater: 'VARCHAR (100)',
    },
}