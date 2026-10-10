from __future__ import annotations

import re
from dataclasses import dataclass, replace

from jobdesk.db import Database
from jobdesk.desired import derive_search_query, extract_keywords, matches_desired
from jobdesk.locations import matches_locations, parse_locations_json
from jobdesk.models import Subscription, Vacancy
from jobdesk.parsers.base import get_registry


@dataclass
class FetchResult:
    new_vacancies: list[Vacancy]
    errors: list[str]
    checked_subscriptions: int
    raw_total: int = 0
    kept_total: int = 0


def _matches_exclude(v: Vacancy, exclude_words: str) -> bool:
    if not exclude_words.strip():
        return False
    hay = f"{v.title} {v.company} {v.description}".lower()
    for word in re.split(r"[,;\n]+", exclude_words):
        w = word.strip().lower()
        if w and w in hay:
            return True
    return False


def _apply_filters(
    items: list[Vacancy],
    sub: Subscription,
    *,
    desired: str,
    use_desired: bool,
    use_post_filter: bool,
    locations: list[str],
) -> list[Vacancy]:
    filtered = [v for v in items if not _matches_exclude(v, sub.exclude_words)]
    if use_desired and use_post_filter and desired:
        filtered = [v for v in filtered if matches_desired(v, desired)]
    if locations:
        filtered = [v for v in filtered if matches_locations(v, locations)]
    return filtered


def run_fetch(db: Database, *, subscription_ids: list[int] | None = None) -> FetchResult:
    registry = get_registry()
    subs = db.list_subscriptions()
    if subscription_ids is not None:
        ids = set(subscription_ids)
        subs = [s for s in subs if s.id in ids]
    subs = [s for s in subs if s.enabled]

    all_new: list[Vacancy] = []
    errors: list[str] = []
    raw_total = 0
    kept_total = 0

    desired = db.get_desired_vacancy().strip()
    use_desired = db.use_desired_vacancy_search() and bool(desired)
    use_post_filter = db.use_desired_post_filter()
    locations = parse_locations_json(db.get_desired_locations())

    if not subs:
        errors.append("Нет включённых подписок — добавьте на вкладке «Подписки».")

    for sub in subs:
        try:
            fetch_sub = _subscription_for_fetch(sub, desired=desired, use_desired=use_desired)
            parser = registry.get(sub.source)
            raw = parser.fetch(fetch_sub)
            if not raw and use_desired:
                short = _fallback_query(desired, fetch_sub.query)
                if short and short != fetch_sub.query:
                    fetch_sub = replace(fetch_sub, query=short)
                    raw = parser.fetch(fetch_sub)
            raw_total += len(raw)
            filtered = _apply_filters(
                raw,
                sub,
                desired=desired,
                use_desired=use_desired,
                use_post_filter=use_post_filter,
                locations=locations,
            )
            kept_total += len(filtered)
            new = db.upsert_vacancies(filtered)
            all_new.extend(new)
            db.touch_subscription_checked(sub.id)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{sub.name}: {exc}")

    if use_desired and raw_total > 0 and kept_total == 0:
        errors.append(
            f"С сайтов получено {raw_total} вакансий, но ни одна не прошла фильтры "
            "(описание, города, исключения). Ослабьте фильтры или снимите города."
        )
    elif raw_total > 0 and kept_total > 0 and not all_new:
        errors.append(
            f"Подошло {kept_total} вакансий, но все уже были в базе. "
            "Снимите «Только новые», чтобы увидеть их в списке."
        )

    return FetchResult(
        new_vacancies=all_new,
        errors=errors,
        checked_subscriptions=len(subs),
        raw_total=raw_total,
        kept_total=kept_total,
    )


def _fallback_query(desired: str, current: str) -> str:
    words = extract_keywords(desired)
    if len(words) >= 2:
        return words[0]
    return derive_search_query(desired) if derive_search_query(desired) != current else ""


def _subscription_for_fetch(
    sub: Subscription,
    *,
    desired: str,
    use_desired: bool,
) -> Subscription:
    if not use_desired:
        return sub
    query = derive_search_query(desired)
    if not query:
        return sub
    return replace(sub, query=query)


def ensure_default_subscription(db: Database) -> None:
    if db.list_subscriptions():
        return
    db.add_subscription(
        name="Python — Хабр RSS",
        source="habr_rss",
        query="python",
        exclude_words="",
    )
