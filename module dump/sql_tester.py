import sqlite3

conn = sqlite3.connect('gamedb.sqlite')
cur = conn.cursor()

def q_generator(amount):
    q_string = '?' + ',?'*(amount-1)
    return(q_string)
    
def select_columns(table_name):
    table_script = 'SELECT * FROM ' + table_name
    cur.execute(table_script)
    columns = [table_name + '.' + desc[0] for desc in cur.description]
    return(columns)
    
game_cols = [col for col in select_columns('Game') if all(tuple(key not in col for key in ('score','id')))]
drive_cols = ['Drive.series', 'Drive.drive_end']
play_cols = select_columns('Play')
selected_cols = tuple(game_cols + drive_cols + play_cols)

script = 'SELECT ' + selected_cols[0]
for col in selected_cols[1:]:
    script = script + ', ' + col



script = script + ''' 
        FROM Game INNER JOIN Drive ON Game.id = Drive.game_id
        INNER JOIN Play ON Drive.id = Play.drive_id;
        '''
cur.execute(script)
play = cur.fetchone()


# # Do some setup
# init_script = open('db_init.sql', 'r')
# cur.executescript(init_script.read())
# conn.commit

# cur.execute('SELECT * FROM Play')
# play_keys = {desc[0] for desc in cur.description if desc[0] != 'id'}
# for key in play_keys:
    # print(key)
    
# new_key = 'rusher'
# sql_type = 'VARCHAR (50)'
# cur.execute('ALTER TABLE Play ADD COLUMN ? VARCHAR(50)', (new_key,))