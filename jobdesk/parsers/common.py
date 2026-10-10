from __future__ import annotations

import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urljoin

from jobdesk.locations import extract_city_from_text
from jobdesk.models import Subscription, Vacancy


def query_words(query: str) -> list[str]:
    q = query.strip().lower()
    if not q:
        return []
    return [w for w in re.split(r"\s+", q) if w]


def filter_by_query(items: list[Vacancy], query: str) -> list[Vacancy]:
    words = query_words(query)
    if not words:
        return items

    def matches(v: Vacancy) -> bool:
        hay = f"{v.title} {v.company} {v.description}".lower()
        return all(w in hay for w in words)

    return [v for v in items if matches(v)]


def make_vacancy(
    *,
    source: str,
    external_id: str,
    title: str,
    url: str,
    company: str = "",
    description: str = "",
    city: str = "",
    published_at: datetime | None = None,
    subscription: Subscription,
) -> Vacancy:
    if not city:
        city = extract_city_from_text(title, description)
    return Vacancy(
        external_id=external_id,
        source=source,
        title=title.strip() or "Без названия",
        company=company.strip(),
        url=url,
        description=description,
        city=city.strip(),
        published_at=published_at,
        subscription_id=subscription.id,
    )


def build_search_url(base: str, param: str, query: str, *, extra: str = "") -> str:
    url = base
    q = query.strip()
    if q:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{param}={quote_plus(q)}"
    if extra:
        url += ("&" if "?" in url else "?") + extra.lstrip("?&")
    return url


def absolute_url(base: str, href: str) -> str:
    return urljoin(base, href)


def parse_rfc822_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def id_from_url(url: str, pattern: str) -> str | None:
    m = re.search(pattern, url)
    return m.group(1) if m else None
