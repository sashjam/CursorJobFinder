import json
import re
import urllib.request

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}


def probe(name: str, url: str) -> None:
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    print("===", name, "len", len(html), "===")
    for pat in (r"/vacancies/\d+", r"/jobs/\d+", r"/vacancy/[a-f0-9]+"):
        ids = list(dict.fromkeys(re.findall(pat, html)))[:8]
        if ids:
            print(pat, ids)
    for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            print("ItemList", len(data.get("itemListElement", [])))
        if isinstance(data, list):
            print("ld+json list", len(data))


probe("getmatch", "https://getmatch.ru/vacancies?q=python")
probe("devby", "https://jobs.devby.io/?search=python")
probe("djini", "https://djini.co/q/?keywords=python")
probe("geekjob", "https://geekjob.ru/vacancies?q=python")
