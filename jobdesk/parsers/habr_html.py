from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from jobdesk.http_client import fetch_text
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser

_HABR_BASE = "https://career.habr.com"


class HabrHtmlParser(JobParser):
    source_id = "habr_html"
    display_name = "Хабр Карьера (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = f"{_HABR_BASE}/vacancies"
        if q:
            url += f"?q={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        vacancies: list[Vacancy] = []
        for card in soup.select("div.vacancy-card"):
            link_el = card.select_one("a.vacancy-card__title-link") or card.select_one(
                "a.vacancy-card__backdrop-link"
            )
            if not link_el or not link_el.get("href"):
                continue
            href = link_el["href"]
            m = re.search(r"/vacancies/(\d+)", href)
            if not m:
                continue
            external_id = m.group(1)
            title = (link_el.get_text(strip=True) or link_el.get("aria-label") or "").strip()
            company_el = card.select_one("a.link-comp")
            company = company_el.get_text(strip=True) if company_el else ""
            time_el = card.select_one("time.basic-date")
            published = None
            if time_el and time_el.get("datetime"):
                try:
                    published = datetime.fromisoformat(time_el["datetime"])
                except ValueError:
                    published = None
            full_url = urljoin(_HABR_BASE, href)
            vacancies.append(
                Vacancy(
                    external_id=external_id,
                    source=self.source_id,
                    title=title,
                    company=company,
                    url=full_url,
                    description="",
                    published_at=published,
                    subscription_id=subscription.id,
                )
            )
        return vacancies
