from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from jobdesk.http_client import fetch_json, fetch_text, hh_headers
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import absolute_url, make_vacancy

_log = logging.getLogger(__name__)


class _HhFamilyHtmlParser(JobParser):
    base_url: str
    search_path: str = "/search/vacancy"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = f"{self.base_url}{self.search_path}?items_on_page=50"
        if q:
            url += f"&text={quote_plus(q)}"
        html = fetch_text(url)
        items = self._parse_search_html(html, subscription)
        if items:
            return items
        if "captcha" in html.lower() or "доступ ограничен" in html.lower():
            raise RuntimeError(
                "hh.ru показал captcha или ограничил доступ. Откройте hh.ru в браузере, "
                "пройдите проверку и повторите позже."
            )
        return items

    def _parse_search_html(self, html: str, subscription: Subscription) -> list[Vacancy]:
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        seen: set[str] = set()

        cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
        if not cards:
            cards = soup.select('[data-qa^="vacancy-serp__vacancy"]')

        for card in cards:
            link = card.select_one('a[data-qa="serp-item__title"]')
            if not link:
                link = card.find("a", href=re.compile(r"/vacancy/\d+"))
            if not link or not link.get("href"):
                continue
            href = link["href"]
            m = re.search(r"/vacancy/(\d+)", href)
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            emp = card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
            addr = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
            title = link.get_text(strip=True) or "Без названия"
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

        if items:
            return items

        for link in soup.find_all("a", href=re.compile(r"^https?://[^/]+/vacancy/\d+")):
            m = re.search(r"/vacancy/(\d+)", link["href"])
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            title = link.get_text(strip=True)
            if not title or len(title) < 2:
                continue
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=m.group(1),
                    title=title,
                    url=link["href"].split("?")[0],
                    company="",
                    description="",
                    city="",
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
    display_name = "🇷🇺 HeadHunter (API → HTML fallback)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        try:
            items = self._fetch_api(subscription)
            if items:
                return items
        except Exception as exc:
            _log.debug("hh API failed, fallback HTML: %s", exc)
        html_items = HhHtmlParser().fetch(subscription)
        return [
            Vacancy(
                external_id=v.external_id,
                source=self.source_id,
                title=v.title,
                company=v.company,
                url=v.url,
                description=v.description,
                city=v.city,
                published_at=v.published_at,
                subscription_id=v.subscription_id,
            )
            for v in html_items
        ]

    def _fetch_api(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://api.hh.ru/vacancies?per_page=50&page=0"
        if q:
            url += f"&text={quote_plus(q)}"
        data = fetch_json(url, headers=hh_headers())
        items: list[Vacancy] = []
        for row in data.get("items", []):
            published = _parse_hh_dt(row.get("published_at"))
            employer = row.get("employer") or {}
            area = (row.get("area") or {}).get("name") or ""
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
                    city=area,
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
