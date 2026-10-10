from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from jobdesk.http_client import fetch_json, fetch_text, hh_headers
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import absolute_url, make_vacancy


class _HhFamilyHtmlParser(JobParser):
    base_url: str
    search_path: str = "/search/vacancy"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = f"{self.base_url}{self.search_path}?items_on_page=50"
        if q:
            url += f"&text={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        for card in soup.select('[data-qa="vacancy-serp__vacancy"]'):
            link = card.find("a", href=re.compile(r"/vacancy/\d+"))
            if not link:
                continue
            href = link["href"]
            m = re.search(r"/vacancy/(\d+)", href)
            if not m:
                continue
            emp = card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
            addr = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
            title = link.get_text(strip=True)
            company = emp.get_text(strip=True) if emp else ""
            city = addr.get_text(strip=True) if addr else ""
            full_url = absolute_url(self.base_url, href.split("?")[0])
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=m.group(1),
                    title=title,
                    url=full_url,
                    company=company,
                    description="",
                    city=city,
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class HhHtmlParser(_HhFamilyHtmlParser):
    source_id = "hh_html"
    display_name = "🇷🇺 HeadHunter / hh.ru (HTML)"
    base_url = "https://hh.ru"


class ZarplataHtmlParser(_HhFamilyHtmlParser):
    source_id = "zarplata_html"
    display_name = "🇷🇺 Zarplata.ru (HTML)"
    base_url = "https://zarplata.ru"


class HhApiParser(JobParser):
    source_id = "hh_api"
    display_name = "🇷🇺 HeadHunter (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://api.hh.ru/vacancies?per_page=50&page=0"
        if q:
            url += f"&text={quote_plus(q)}"
        try:
            data = fetch_json(url, headers=hh_headers())
        except Exception as exc:
            raise RuntimeError(
                f"API hh.ru недоступен ({exc}). Используйте источник «HeadHunter (HTML)» "
                "или задайте JOBDESK_HH_USER_AGENT=App/1.0 (your@email.com)"
            ) from exc
        items: list[Vacancy] = []
        for row in data.get("items", []):
            published = _parse_hh_dt(row.get("published_at"))
            employer = row.get("employer") or {}
            vid = str(row.get("id", ""))
            alt = row.get("alternate_url") or f"https://hh.ru/vacancy/{vid}"
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=vid,
                    title=row.get("name") or "Без названия",
                    url=alt,
                    company=employer.get("name") or "",
                    description="",
                    published_at=published,
                    subscription=subscription,
                )
            )
        return items


def _parse_hh_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
