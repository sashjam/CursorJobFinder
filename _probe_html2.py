import re
import ssl
import urllib.request

import certifi
from bs4 import BeautifulSoup

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}
CTX = ssl.create_default_context(cafile=certifi.where())


def soup(url: str) -> BeautifulSoup:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
        return BeautifulSoup(r.read(), "lxml")


def superjob():
    s = soup("https://www.superjob.ru/vakansii/programmist-python.html")
    for sel in (
        "[data-test='vacancy-item']",
        ".f-test-search-result-item",
        "div._1ID8B",
        "a[href*='/vakansii/']",
    ):
        n = len(s.select(sel))
        if n:
            print("superjob", sel, n)
    link = s.find("a", href=re.compile(r"/vakansii/\d+"))
    if link:
        print("sample", link["href"], link.get_text(strip=True)[:60])


def trudvsem():
    s = soup("https://trudvsem.ru/vacancy/search?text=python")
    links = s.find_all("a", href=re.compile(r"/vacancy/card/"))
    print("trudvsem card links", len(links))
    if links:
        print(links[0]["href"], links[0].get_text(strip=True)[:60])


def djini():
    s = soup("https://djini.co/q/?keywords=python")
    for link in s.find_all("a", href=re.compile(r"^/vacancy/[a-f0-9]+$")):
        print("djini", link["href"], link.get_text(strip=True)[:60])
        break


if __name__ == "__main__":
    superjob()
    trudvsem()
    djini()
