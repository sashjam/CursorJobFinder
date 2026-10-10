from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from jobdesk.http_client import fetch_json, fetch_text
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import absolute_url, make_vacancy


class SuperjobHtmlParser(JobParser):
    source_id = "superjob_html"
    display_name = "🇷🇺 SuperJob (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://www.superjob.ru/vacancy/search/?keywords={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        for block in soup.select(".f-test-search-result-item"):
            link = block.find("a", href=re.compile(r"/vakansii/.+\d+\.html"))
            if not link:
                continue
            href = link["href"]
            m = re.search(r"-(\d+)\.html", href)
            if not m:
                continue
            title = link.get_text(" ", strip=True)
            company_el = block.select_one(".f-test-text-vacancy-item-company-name")
            company = company_el.get_text(strip=True) if company_el else ""
            full_url = absolute_url("https://www.superjob.ru", href)
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=m.group(1),
                    title=title,
                    url=full_url,
                    company=company,
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class RabotaRuHtmlParser(JobParser):
    source_id = "rabota_html"
    display_name = "🇷🇺 Rabota.ru (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://www.rabota.ru/vacancy?query={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        seen: set[str] = set()
        for link in soup.find_all("a", href=re.compile(r"^/vacancy/\d+")):
            href = link["href"]
            m = re.match(r"^/vacancy/(\d+)", href)
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=m.group(1),
                    title=title,
                    url=absolute_url("https://www.rabota.ru", href),
                    company="",
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class TrudvsemApiParser(JobParser):
    source_id = "trudvsem_api"
    display_name = "🇷🇺 Работа России / Трудвсем (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = (
            "https://opendata.trudvsem.ru/api/v1/vacancies"
            f"?text={quote_plus(q)}&limit=50&offset=0"
        )
        data = fetch_json(url)
        vacancies = data.get("results", {}).get("vacancies", [])
        items: list[Vacancy] = []
        for wrap in vacancies:
            v = wrap.get("vacancy") or wrap
            vid = str(v.get("id") or v.get("vac_url") or "")
            if not vid:
                continue
            company = (v.get("company") or {}).get("name") or ""
            title = v.get("job-name") or "Без названия"
            vac_url = v.get("vac_url") or f"https://trudvsem.ru/vacancy/card/{vid}"
            published = _parse_tv_date(v.get("creation-date"))
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=vid,
                    title=title,
                    url=vac_url,
                    company=company,
                    description=(v.get("duty") or "")[:500],
                    published_at=published,
                    subscription=subscription,
                )
            )
        return items


def _parse_tv_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value[:10], fmt)
        except ValueError:
            continue
    return None
