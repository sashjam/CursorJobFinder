import re
import ssl
import urllib.request

import certifi
from bs4 import BeautifulSoup

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}
CTX = ssl.create_default_context(cafile=certifi.where())
req = urllib.request.Request(
    "https://www.superjob.ru/vakansii/programmist-python.html", headers=UA
)
html = urllib.request.urlopen(req, timeout=25, context=CTX).read()
soup = BeautifulSoup(html, "lxml")
item = soup.select_one(".f-test-search-result-item")
if item:
    print(item.prettify()[:2000])
