from __future__ import annotations

import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from jobdesk.http_client import fetch_text
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import JobParser
from jobdesk.parsers.common import absolute_url, make_vacancy
class DouHtmlParser(JobParser):
    source_id = "dou_html"
    display_name = "🇺🇦 DOU (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip()
        url = "https://jobs.dou.ua/vacancies/"
        if q:
            url += f"?search={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        for li in soup.select("li.l-vacancy"):
            link = li.select_one("a.vt")
            if not link or not link.get("href"):
                continue
            href = link["href"]
            m = re.search(r"/vacancies/(\d+)", href)
            ext = m.group(1) if m else href
            company_el = li.select_one("a.company")
            company = company_el.get_text(strip=True) if company_el else ""
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=str(ext),
                    title=link.get_text(strip=True),
                    url=href if href.startswith("http") else absolute_url("https://jobs.dou.ua", href),
                    company=company,
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class DevByHtmlParser(JobParser):
    source_id = "devby_html"
    display_name = "🇧🇾 Dev.by (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://jobs.devby.io/?search={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        seen: set[str] = set()
        for link in soup.find_all("a", href=re.compile(r"^/vacancies/\d+")):
            href = link["href"]
            m = re.match(r"^/vacancies/(\d+)", href)
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            title = link.get_text(strip=True)
            if not title:
                continue
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=m.group(1),
                    title=title,
                    url=absolute_url("https://jobs.devby.io", href),
                    company="",
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class DjiniHtmlParser(JobParser):
    source_id = "djini_html"
    display_name = "🇺🇦 Djini (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://djini.co/q/?keywords={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        seen: set[str] = set()
        for li in soup.select("li.collection-item"):
            link = li.find("a", href=re.compile(r"^/vacancy/[a-f0-9]+$"))
            if not link:
                continue
            href = link["href"]
            ext = href.rsplit("/", 1)[-1]
            if ext in seen:
                continue
            seen.add(ext)
            title_el = li.select_one("h2") or li.select_one(".title") or link
            title = title_el.get_text(strip=True) if title_el else ext
            company_el = li.select_one(".company") or li.select_one("a.company")
            company = company_el.get_text(strip=True) if company_el else ""
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=ext,
                    title=title,
                    url=absolute_url("https://djini.co", href),
                    company=company,
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items


class GeekjobHtmlParser(JobParser):
    source_id = "geekjob_html"
    display_name = "🇷🇺 GeekJob (HTML)"

    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        q = subscription.query.strip() or "python"
        url = f"https://geekjob.ru/vacancies?q={quote_plus(q)}"
        html = fetch_text(url)
        soup = BeautifulSoup(html, "lxml")
        items: list[Vacancy] = []
        seen: set[str] = set()
        for link in soup.find_all("a", href=re.compile(r"^/vacancy/[a-f0-9]+$")):
            href = link["href"]
            ext = href.rsplit("/", 1)[-1]
            if ext in seen:
                continue
            seen.add(ext)
            title = link.get_text(" ", strip=True)
            if not title or len(title) < 4:
                parent = link.find_parent("article")
                if parent:
                    h = parent.find(["h2", "h3"])
                    title = h.get_text(strip=True) if h else ext
            items.append(
                make_vacancy(
                    source=self.source_id,
                    external_id=ext,
                    title=title or ext,
                    url=absolute_url("https://geekjob.ru", href),
                    company="",
                    description="",
                    published_at=None,
                    subscription=subscription,
                )
            )
        return items
