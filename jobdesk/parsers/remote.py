from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

from jobdesk.http_client import fetch_json
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import filter_by_query, make_vacancy


class RemoteOkParser(JobParser):
    source_id = "remoteok_api"
    display_name = "🌍 Remote OK (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        data = fetch_json("https://remoteok.com/api")
        if not isinstance(data, list):
            return []
        items: list[Vacancy] = []
        for row in data:
            if not isinstance(row, dict) or "id" not in row:
                continue
            slug = row.get("slug") or str(row["id"])
            url = row.get("url") or f"https://remoteok.com/remote-jobs/{slug}"
            title = row.get("position") or row.get("title") or "Без названия"
            company = row.get("company") or ""
            desc = (row.get("description") or "")[:500]
            published = _epoch_or_date(row.get("epoch"), row.get("date"))
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=str(row["id"]),
                    title=str(title),
                    url=str(url),
                    company=str(company),
                    description=desc,
                    published_at=published,
                    subscription=subscription,
                )
            )
        return filter_by_query(items, subscription.query)


class RemotiveParser(JobParser):
    source_id = "remotive_api"
    display_name = "🌍 Remotive (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://remotive.com/api/remote-jobs"
        if q:
            url += f"?search={quote_plus(q)}"
        data = fetch_json(url)
        jobs = data.get("jobs") or []
        items: list[Vacancy] = []
        for row in jobs:
            jid = str(row.get("id") or row.get("url") or row.get("title"))
            job_url = row.get("url") or f"https://remotive.com/remote-jobs/{jid}"
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=jid,
                    title=row.get("title") or "Без названия",
                    url=job_url,
                    company=row.get("company_name") or "",
                    description=(row.get("description") or "")[:500],
                    published_at=_parse_iso(row.get("publication_date")),
                    subscription=subscription,
                )
            )
        if q and "search=" not in url:
            return filter_by_query(items, q)
        return items


class JobicyParser(JobParser):
    source_id = "jobicy_api"
    display_name = "🌍 Jobicy (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={quote_plus(q)}"
        data = fetch_json(url)
        items: list[Vacancy] = []
        for row in data.get("jobs") or []:
            jid = str(row.get("id") or row.get("jobSlug"))
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=jid,
                    title=row.get("jobTitle") or "Без названия",
                    url=row.get("url") or f"https://jobicy.com/jobs/{row.get('jobSlug', jid)}",
                    company=row.get("companyName") or "",
                    description=(row.get("jobExcerpt") or "")[:500],
                    published_at=_parse_iso(row.get("pubDate")),
                    subscription=subscription,
                )
            )
        return items


class ArbeitnowParser(JobParser):
    source_id = "arbeitnow_api"
    display_name = "🌍 Arbeitnow (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        data = fetch_json("https://www.arbeitnow.com/api/job-board-api")
        rows = data.get("data") or []
        items: list[Vacancy] = []
        for row in rows:
            slug = str(row.get("slug") or row.get("url"))
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=slug,
                    title=row.get("title") or "Без названия",
                    url=row.get("url") or f"https://www.arbeitnow.com/jobs/{slug}",
                    company=row.get("company_name") or "",
                    description=(row.get("description") or "")[:500],
                    published_at=_parse_iso(row.get("created_at")),
                    subscription=subscription,
                )
            )
        return filter_by_query(items, subscription.query)


class HimalayasParser(JobParser):
    source_id = "himalayas_api"
    display_name = "🌍 Himalayas (API)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://himalayas.app/jobs/api?limit=50"
        if q:
            url += f"&search={quote_plus(q)}"
        data = fetch_json(url)
        jobs = data.get("jobs") if isinstance(data, dict) else []
        items: list[Vacancy] = []
        for row in jobs or []:
            guid = str(row.get("guid") or row.get("companySlug") or row.get("title"))
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=guid,
                    title=row.get("title") or "Без названия",
                    url=row.get("applicationLink") or "https://himalayas.app/jobs",
                    company=row.get("companyName") or "",
                    description=(row.get("excerpt") or "")[:500],
                    published_at=_parse_iso(row.get("pubDate")),
                    subscription=subscription,
                )
            )
        if q and "search=" not in url:
            return filter_by_query(items, q)
        return items


def _parse_iso(value: object | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(int(value))
        except (OSError, ValueError, OverflowError):
            return None
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _epoch_or_date(epoch: object, date_str: object) -> datetime | None:
    if epoch is not None:
        try:
            return datetime.utcfromtimestamp(int(epoch))
        except (TypeError, ValueError, OSError):
            pass
    if date_str:
        try:
            return parsedate_to_datetime(str(date_str))
        except (TypeError, ValueError, IndexError):
            pass
    return None
