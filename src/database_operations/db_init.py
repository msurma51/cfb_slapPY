# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 22:42:11 2024

@author: surma
"""

import os
import sqlite3

def db_init(data_path, db_name, init_script):
    # Create / get data path
    if not os.path.exists(data_path):
        os.mkdir(data_path)
        print('initialized data path')
    
    # Create / get DB and run script
    conn = sqlite3.connect(os.path.join(data_path, db_name))
    cur = conn.cursor()
    cur.executescript(init_script.read())
    conn.commit()

if __name__ == "__main__":
    data_path = '..\\..\\data'
    db_name = 'slapPY_DB.sqlite'
    init_script = open('db_init.sql', 'r')
    db_init(data_path, db_name, init_script)
    