from __future__ import annotations

import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser

from jobdesk.http_client import fetch_bytes
from jobdesk.locations import extract_city_from_text
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser

_HABR_BASE = "https://career.habr.com"


class HabrRssParser(JobParser):
    source_id = "habr_rss"
    display_name = "Хабр Карьера (RSS)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = f"{_HABR_BASE}/vacancies/rss?per_page=50"
        if q:
            url += f"&q={quote_plus(q)}"
        raw = fetch_bytes(url)
        feed = feedparser.parse(raw)
        vacancies: list[Vacancy] = []
        for entry in feed.entries:
            guid = getattr(entry, "guid", "") or getattr(entry, "id", "") or entry.link
            external_id = _external_id_from_guid(guid, entry.link)
            published = _parse_pub_date(entry)
            company = ""
            if getattr(entry, "author", None):
                company = entry.author
            else:
                company = _company_from_title(entry.title)
            raw_title = entry.title or ""
            desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            title = _clean_title(raw_title)
            city = extract_city_from_text(raw_title, desc)
            vacancies.append(
                Vacancy(
                    external_id=external_id,
                    source=self.source_id,
                    title=title,
                    company=company,
                    url=entry.link,
                    description=desc,
                    city=city,
                    published_at=published,
                    subscription_id=subscription.id,
                )
            )
        return vacancies


def _external_id_from_guid(guid: str, link: str) -> str:
    m = re.search(r"/vacancies/(\d+)", link or guid)
    if m:
        return m.group(1)
    return guid or link


def _parse_pub_date(entry: feedparser.FeedParserDict) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    if getattr(entry, "published", None):
        try:
            return parsedate_to_datetime(entry.published)
        except (TypeError, ValueError, IndexError):
            pass
    return None


def _company_from_title(title: str) -> str:
    m = re.match(r"^Требуется «.+» \((.+)\)$", title.strip())
    if m:
        return ""
    m = re.search(r"Компания «([^»]+)»", title)
    return m.group(1) if m else ""


def _clean_title(title: str) -> str:
    title = title.strip()
    m = re.match(r"^Требуется «([^»]+)»", title)
    if m:
        return m.group(1)
    return title
