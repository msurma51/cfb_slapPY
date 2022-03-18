import sqlite3
import json

conn = sqlite3.connect('gamedb.sqlite')
cur = conn.cursor()

# Do some setup
init_script = open('db_init.sql', 'r')
cur.executescript(init_script.read())

fname = input('Enter file name: ')
if len(fname) < 1:
    fname = 'lycoming.json'

str_data = open(fname).read()
schedule = json.loads(str_data)
# Create a list including just the game data for each game
games = [schedule[game_key] for game_key in schedule.keys() if '@' in game_key]

def script_maker(table,keys):
    script = 'INSERT OR IGNORE INTO ' + table + ' ('
    for key in keys[:-1]:
        script = script + key + ','
    script = script + keys[-1] + ') VALUES (' + '?,'*(len(keys)-1) + '?);'
    return(script)

for game_info in games:
    # Grab end game state from game
    state = game_info['state']
    # Select keys to include in SQL insert script
    game_keys = [key for key in state if any(('home' in key, 'away' in key, 'score' in key,
                 'choice' in key, 'open' in key, 'won' in key)) and 'tol' not in key]
    game_script = script_maker('Game',game_keys)
    game_values = tuple(state[key] for key in game_keys)
    cur.execute(game_script, game_values)
    game = game_info['game']
    series = 1
    for drive in game:
        info = drive[0]
        cur.execute('SELECT id FROM Game WHERE home_abbr = ? AND away_abbr = ? ',(info['home_abbr'],info['away_abbr']))
        game_id = cur.fetchone()[0]
        info.update({'series':series, 'game_id':game_id})
        drive_keys = [info_key for info_key in info.keys() if all(('name' not in info_key,'abbr' not in info_key,':' not in str(info[info_key])))]
        if 'drive_start' in drive_keys:
            drive_keys.remove('drive_start')
        drive_script = script_maker('Drive', drive_keys)
        drive_values = tuple(info[key] for key in drive_keys)
        cur.execute(drive_script, drive_values)
        series += 1
    conn.commit()
    



# for entry in json_data:

    # name = entry[0]
    # title = entry[1]
    # role = entry[2]

    # print((name, title, role))

    # cur.execute('''INSERT OR IGNORE INTO User (name)
        # VALUES ( ? )''', ( name, ) )
    # cur.execute('SELECT id FROM User WHERE name = ? ', (name, ))
    # user_id = cur.fetchone()[0]

    # cur.execute('''INSERT OR IGNORE INTO Course (title)
        # VALUES ( ? )''', ( title, ) )
    # cur.execute('SELECT id FROM Course WHERE title = ? ', (title, ))
    # course_id = cur.fetchone()[0]

    # cur.execute('''INSERT OR REPLACE INTO Member
        # (user_id, course_id, role) VALUES ( ?, ?, ? )''',
        # ( user_id, course_id, role ) )

    # conn.commit()
