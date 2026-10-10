from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from jobdesk.models import Subscription, Vacancy


class JobParser(ABC):
    source_id: ClassVar[str]
    display_name: ClassVar[str]

    @abstractmethod
    def fetch(self, subscription: Subscription) -> list[Vacancy]:
        raise NotImplementedError


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, JobParser] = {}

    def register(self, parser: JobParser) -> None:
        self._parsers[parser.source_id] = parser

    def get(self, source_id: str) -> JobParser:
        if source_id not in self._parsers:
            raise KeyError(f"Unknown source: {source_id}")
        return self._parsers[source_id]

    def list_sources(self) -> list[tuple[str, str]]:
        items = [(p.source_id, p.display_name) for p in self._parsers.values()]
        return sorted(items, key=lambda x: x[1].lower())


_registry: ParserRegistry | None = None


def get_registry() -> ParserRegistry:
    global _registry
    if _registry is None:
        from jobdesk.parsers.register import populate_registry

        _registry = ParserRegistry()
        populate_registry(_registry)
    return _registry
