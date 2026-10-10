import urllib.request

req = urllib.request.Request(
    "https://career.habr.com/robots.txt",
    headers={"User-Agent": "JobDesk/1.0 (personal job search)"},
)
text = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
open(r"d:\_PHPStormProjects\Job\_robots.txt", "w", encoding="utf-8").write(text)
print("lines", len(text.splitlines()))
