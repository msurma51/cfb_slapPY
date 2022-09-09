import urllib.request
from bs4 import BeautifulSoup

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 

def pot(headers, url, strainer = None):
    request = urllib.request.Request(url,None,headers) #The assembled request
    response = urllib.request.urlopen(request)
    html = response.read().decode(errors='ignore') # The data u need
    if strainer:
        return BeautifulSoup(html, "html.parser", parse_only=strainer)
    else:
        return(BeautifulSoup(html, "html.parser"))