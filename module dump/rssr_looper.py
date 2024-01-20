import subprocess as sp

year = input('Enter recruiting year')
for i in range(2,6):
	proc = sp.run(['python','rssr.py'], input='{}\n{}'.format(year,i), text=True)
