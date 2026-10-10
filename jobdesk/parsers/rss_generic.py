from __future__ import annotations

import re
from urllib.parse import quote_plus, urlparse

import feedparser

from jobdesk.http_client import fetch_bytes
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import make_vacancy, parse_rfc822_date
from jobdesk.parsers.habr_rss import _clean_title, _external_id_from_guid


class CustomRssParser(JobParser):
    """Полный URL RSS/Atom в поле «Запрос»."""

    source_id = "rss_custom"
    display_name = "📡 Произвольный RSS"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        url = subscription.query.strip()
        if not url:
            raise ValueError("Укажите URL RSS-ленты в поле «Запрос»")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL должен начинаться с http:// или https://")
        feed = feedparser.parse(fetch_bytes(url))
        items: list[Vacancy] = []
        for entry in feed.entries:
            link = getattr(entry, "link", "") or ""
            guid = getattr(entry, "guid", "") or getattr(entry, "id", "") or link
            external_id = _external_id_from_guid(guid, link)
            if not external_id:
                external_id = re.sub(r"[^\w.-]+", "_", link)[-120:]
            company = getattr(entry, "author", "") or ""
            title = _clean_title(getattr(entry, "title", "") or "Без названия")
            desc = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=external_id,
                    title=title,
                    url=link,
                    company=company,
                    description=desc,
                    published_at=parse_rfc822_date(getattr(entry, "published", None)),
                    subscription=subscription,
                )
            )
        return items


class DouRssParser(JobParser):
    source_id = "dou_rss"
    display_name = "🇺🇦 DOU (RSS)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://jobs.dou.ua/vacancies/feeds/"
        if q:
            url += f"?search={quote_plus(q)}"
        return _fetch_dou_rss(url, self.source_id, subscription)


class WeWorkRemotelyRssParser(JobParser):
    source_id = "wwr_rss"
    display_name = "🌍 We Work Remotely (RSS)"

    FEEDS = {
        "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        "design": "https://weworkremotely.com/categories/remote-design-jobs.rss",
        "all": "https://weworkremotely.com/remote-jobs.rss",
    }

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        key = subscription.query.strip().lower() or "programming"
        if key.startswith("http"):
            url = key
        else:
            url = self.FEEDS.get(key, self.FEEDS["programming"])
        feed = feedparser.parse(fetch_bytes(url))
        items: list[Vacancy] = []
        for entry in feed.entries:
            link = entry.link
            ext = id_from_path(link)
            title = entry.title or "Без названия"
            company = ""
            if ":" in title:
                company, _, title = title.partition(":")
                company = company.strip()
                title = title.strip()
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=ext or link,
                    title=title,
                    url=link,
                    company=company,
                    description=getattr(entry, "summary", "") or "",
                    published_at=parse_rfc822_date(getattr(entry, "published", None)),
                    subscription=subscription,
                )
            )
        return items


def id_from_path(link: str) -> str:
    m = re.search(r"/remote-jobs/([^/?#]+)", link)
    return m.group(1) if m else link


def _fetch_dou_rss(url: str, source_id: str, subscription: Subscription) -> list[Vacancy]:
    feed = feedparser.parse(fetch_bytes(url))
    items: list[Vacancy] = []
    for entry in feed.entries:
        link = entry.link
        m = re.search(r"/vacancies/(\d+)", link)
        external_id = m.group(1) if m else link
        title = entry.title or "Без названия"
        items.append(
            make_vacancy(
                source=source_id,
                external_id=external_id,
                title=title,
                url=link,
                company="",
                description=getattr(entry, "summary", "") or "",
                published_at=parse_rfc822_date(getattr(entry, "published", None)),
                subscription=subscription,
            )
        )
    return items
