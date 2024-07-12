# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 22:42:11 2024

@author: surma
"""

from db_funcs import db_connect, db_write, create_script_builder
from table_configs import tables

data_path = '..\\..\\data'
db_name = 'slapPY_DB.sqlite'
conn = db_connect(data_path, db_name)
script_list = [create_script_builder(table, column_dict) for table, column_dict in tables.items()]
init_script = '; '.join(script_list)
db_write(conn, script = init_script)
    