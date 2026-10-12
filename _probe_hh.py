import re
import urllib.error
import urllib.request

from bs4 import BeautifulSoup

from jobdesk.config import ensure_env_loaded, hh_user_agent
from jobdesk.http_client import fetch_json, fetch_text, hh_headers
from jobdesk.models import Subscription
from jobdesk.parsers.hh import HhApiParser, HhHtmlParser

ensure_env_loaded()

sub = Subscription(
    id=1,
    name="t",
    source="hh",
    query="python",
    exclude_words="",
    enabled=True,
    last_checked_at=None,
)

print("hh_user_agent:", hh_user_agent())
print("hh_headers:", hh_headers())

try:
    data = fetch_json(
        "https://api.hh.ru/vacancies?text=python&per_page=3",
        headers=hh_headers(),
    )
    print("API items", len(data.get("items", [])))
except Exception as e:
    print("API fail", e)

try:
    n = len(HhApiParser().fetch(sub))
    print("HhApiParser", n)
except Exception as e:
    print("HhApiParser fail", e)

try:
    n = len(HhHtmlParser().fetch(sub))
    print("HhHtmlParser", n)
except Exception as e:
    print("HhHtmlParser fail", e)

html = fetch_text("https://hh.ru/search/vacancy?text=python&items_on_page=10")
print("html len", len(html))
soup = BeautifulSoup(html, "lxml")
for sel in (
    '[data-qa="vacancy-serp__vacancy"]',
    '[data-qa^="vacancy-serp"]',
    'a[href*="/vacancy/"]',
):
    print(sel, len(soup.select(sel)))
if "captcha" in html.lower() or "Доступ ограничен" in html:
    print("BLOCKED or captcha page")
