import json

infile = open('parsed_games_2022.json').read()
link_list = json.loads(infile)
d = dict()
with open('parsed_games_2022.json','w') as outfile:
    json.dump([d,*link_list[1:]],outfile)