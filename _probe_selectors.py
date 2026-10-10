import re
import urllib.request
from bs4 import BeautifulSoup

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}


def fetch(url: str) -> BeautifulSoup:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return BeautifulSoup(r.read(), "lxml")


def hh():
    soup = fetch("https://hh.ru/search/vacancy?text=python&items_on_page=5")
    for card in soup.select('[data-qa="vacancy-serp__vacancy"]')[:2]:
        link = card.find("a", href=re.compile(r"/vacancy/\d+"))
        emp = card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
        print("hh", link["href"] if link else None, link.get_text(strip=True)[:50] if link else None)
        print("   emp", emp.get_text(strip=True) if emp else None)


def geekjob():
    soup = fetch("https://geekjob.ru/vacancies?q=python")
    for art in soup.find_all("article")[:3]:
        link = art.find("a", href=re.compile(r"/vacancy/"))
        print("geekjob", link["href"] if link else None, link.get_text(strip=True)[:50] if link else None)


def dou():
    soup = fetch("https://jobs.dou.ua/vacancies/?search=python")
    for li in soup.select("li.l-vacancy")[:2]:
        link = li.select_one("a.vt")
        company = li.select_one("a.company")
        print("dou", link["href"] if link else None, link.get_text(strip=True)[:50] if link else None)
        print("   co", company.get_text(strip=True) if company else None)


def devby():
    soup = fetch("https://jobs.devby.io/?search=python")
    seen = set()
    for link in soup.find_all("a", href=re.compile(r"^/jobs/\d+")):
        if link["href"] in seen:
            continue
        seen.add(link["href"])
        print("devby", link["href"], link.get_text(strip=True)[:50])
        if len(seen) >= 3:
            break


def djini():
    soup = fetch("https://djini.co/q/?keywords=python")
    seen = set()
    for link in soup.find_all("a", href=re.compile(r"^/jobs/\d+")):
        if link["href"] in seen:
            continue
        seen.add(link["href"])
        print("djini", link["href"], link.get_text(strip=True)[:50])
        if len(seen) >= 3:
            break


def getmatch():
    soup = fetch("https://getmatch.ru/vacancies?q=python")
    seen = set()
    for link in soup.find_all("a", href=re.compile(r"/vacancies/\d+")):
        href = link["href"]
        if href in seen:
            continue
        seen.add(href)
        print("getmatch", href, link.get_text(strip=True)[:50])
        if len(seen) >= 3:
            break


if __name__ == "__main__":
    hh()
    geekjob()
    dou()
    devby()
    djini()
    getmatch()
