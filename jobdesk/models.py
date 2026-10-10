from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Vacancy:
    external_id: str
    source: str
    title: str
    company: str
    url: str
    description: str
    published_at: datetime | None
    city: str = ""
    subscription_id: int | None = None

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.external_id}"


@dataclass(frozen=True, slots=True)
class Subscription:
    id: int
    name: str
    source: str
    query: str
    exclude_words: str
    enabled: bool
    last_checked_at: datetime | None
