import json

infile = open('parsed_schedules.json').read()
link_list = json.loads(infile)
link_dict = link_list[0]
link_archive = link_list[1]
link_dump = []

with open('parsed_schedules.json', 'w') as outfile:
    json.dump([link_dict,link_archive,link_dump],outfile)