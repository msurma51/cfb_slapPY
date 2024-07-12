# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:26:06 2024

@author: surma
"""

import os
import sqlite3
import pandas as pd

def db_connect(data_path, db_name):
    # Create / get data path
    if not os.path.exists(data_path):
        os.mkdir(data_path)
        print('initialized data path')
    
    # Create / get DB and run script
    return sqlite3.connect(os.path.join(data_path, db_name))
    
def db_write(conn, query = '', script = None):
    cur = conn.cursor()
    if not script:
        if len(query) > 0:
            cur.execute(query)
        else:
            print('No query or script provided')    
    else: 
        cur.executescript(script)
    conn.commit()
    
def create_script_builder(table, column_dict):
    column_types = [' '.join((column, dtype)) for column, dtype in column_dict.items()]
    column_statement = ', '.join(column_types)
    return f'DROP TABLE IF EXISTS {table}; CREATE TABLE {table} ({column_statement})'
    
def db_insert_from_pd(conn, table, df, col_set = None):
    cur = conn.cursor()
    if col_set:
        columns = col_set
    else:
        columns = df.columns.values.tolist()
    col_string = ', '.join(columns)
    col_ref_string = ', '.join([':' + column for column in columns])
    query = f"INSERT OR IGNORE INTO {table} ({col_string}) VALUES ({col_ref_string})"
    data = tuple(df[columns].to_dict(orient = 'index').values())
    cur.executemany(query, data)
    conn.commit()
    
    