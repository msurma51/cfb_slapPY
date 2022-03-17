import sqlite3

conn = sqlite3.connect('gamedb.sqlite')
cur = conn.cursor()

# Do some setup
init_script = open('db_init.sql', 'r')
cur.executescript(init_script.read())
conn.commit