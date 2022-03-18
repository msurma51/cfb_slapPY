import json

fname = input('Enter file name: ')
if len(fname) < 1:
    fname = 'lycoming.json'

str_data = open(fname).read()
schedule = json.loads(str_data)

games = [schedule[game_key] for game_key in schedule.keys() if '@' in game_key]

def script_maker(table,keys):
    script = 'INSERT OR IGNORE INTO ' + table + ' ('
    for key in keys[:-1]:
        script = script + key + ','
    script = script + keys[-1] + ') VALUES (' + '?,'*(len(keys)-1) + '?);'
    return(script)


for game in games:
    # Grab end game state from game
    state = game['state']
    # Select keys to include in SQL insert script
    game_keys = [key for key in state if any(('home' in key, 'away' in key, 'score' in key,
                 'choice' in key, 'open' in key, 'won' in key)) and 'tol' not in key]
    # Initialize script
    game_script = script_maker('Game',game_keys)
    
print(game_script)