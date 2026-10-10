import json
import re
import urllib.request

UA = {"User-Agent": "JobDesk/1.0 (personal job search)"}
html = urllib.request.urlopen(
    urllib.request.Request("https://getmatch.ru/vacancies?q=python", headers=UA),
    timeout=25,
).read().decode("utf-8", "replace")

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if m:
    data = json.loads(m.group(1))
    props = data.get("props", {}).get("pageProps", {})
    print("pageProps keys", props.keys())
    for k, v in props.items():
        if isinstance(v, list):
            print(k, "list", len(v))
            if v and isinstance(v[0], dict):
                print(" sample keys", v[0].keys())
        elif isinstance(v, dict):
            print(k, "dict keys", list(v.keys())[:10])

for pat in (r"vacancyId", r"/api/", r"vacancies"):
    print(pat, html.count(pat))

print("numeric ids", re.findall(r'"id":(\d{4,})', html)[:10])
print("paths", re.findall(r'href="(/[^"]*vacan[^"]*)"', html)[:15])
