'''
import urllib.request
import ssl

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
if len(url) < 1:
    url = 'file:///C:/Users/surma/Downloads/Franklin%20&%20Marshall%20at%20Lebanon%20Valley%20-%20September%204,%202021%20-%201%20p.m.%20-%20Box%20Score%20-%20Franklin%20&%20Marshall%20Athletics.html'
fname = 'dips.html'
urllib.request.urlretrieve(url,fname)
html = urlopen(fname, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")
'''
import urllib.request
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'

url = 'https://godiplomats.com/sports/m-footbl/2021-22/boxscores/20210904_yzfh.xml?view=plays'
headers={'User-Agent':user_agent,} 

request=urllib.request.Request(url,None,headers) #The assembled request
response = urllib.request.urlopen(request)
html = response.read().decode() # The data u need
soup = BeautifulSoup(html, "html.parser")