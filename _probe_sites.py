import json
import re
import urllib.request
from bs4 import BeautifulSoup

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def probe(name: str, url: str) -> None:
    print("===", name, "===")
    html = fetch(url)
    soup = BeautifulSoup(html, "lxml")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"vacan|/jobs/|/job/", href, re.I):
            cls = " ".join(a.get("class") or [])[:40]
            text = a.get_text(strip=True)[:60]
            if text:
                print(" ", href[:80], "|", cls, "|", text)
    print()


probe("geekjob", "https://geekjob.ru/vacancies?q=python")
probe("dou", "https://jobs.dou.ua/vacancies/?search=python")
probe("devby", "https://jobs.devby.io/?search=python")
probe("getmatch", "https://getmatch.ru/vacancies?q=python")
