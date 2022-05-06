names_in = open('names.txt', 'r')
names_out = open('namespace.py', 'w')
names = names_in.readlines()
for name in names:
    name = name.strip()
    assign = "{}='{}'\n".format(name,name)
    names_out.write(assign)
    