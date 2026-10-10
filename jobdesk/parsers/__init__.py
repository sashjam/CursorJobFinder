from jobdesk.parsers.base import ParserRegistry, get_registry
from jobdesk.parsers.habr_html import HabrHtmlParser
from jobdesk.parsers.habr_rss import HabrRssParser

__all__ = [
    "ParserRegistry",
    "get_registry",
    "HabrRssParser",
    "HabrHtmlParser",
]
