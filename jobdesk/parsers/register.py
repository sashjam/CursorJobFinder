from __future__ import annotations

from jobdesk.parsers.base import ParserRegistry
from jobdesk.parsers.cis import DevByHtmlParser, DjiniHtmlParser, DouHtmlParser, GeekjobHtmlParser
from jobdesk.parsers.habr_html import HabrHtmlParser
from jobdesk.parsers.habr_rss import HabrRssParser
from jobdesk.parsers.hh import HhApiParser, HhHtmlParser, ZarplataHtmlParser
from jobdesk.parsers.remote import (
    ArbeitnowParser,
    HimalayasParser,
    JobicyParser,
    RemotiveParser,
    RemoteOkParser,
)
from jobdesk.parsers.rss_generic import CustomRssParser, DouRssParser, WeWorkRemotelyRssParser
from jobdesk.parsers.russia import RabotaRuHtmlParser, SuperjobHtmlParser, TrudvsemApiParser

# Порядок = порядок в выпадающем списке (группы по эмодзи-региону).
ALL_PARSERS = [
    HabrRssParser,
    HabrHtmlParser,
    HhHtmlParser,
    HhApiParser,
    ZarplataHtmlParser,
    SuperjobHtmlParser,
    RabotaRuHtmlParser,
    TrudvsemApiParser,
    GeekjobHtmlParser,
    DouHtmlParser,
    DouRssParser,
    DevByHtmlParser,
    DjiniHtmlParser,
    RemoteOkParser,
    RemotiveParser,
    JobicyParser,
    ArbeitnowParser,
    HimalayasParser,
    WeWorkRemotelyRssParser,
    CustomRssParser,
]


def populate_registry(registry: ParserRegistry) -> None:
    for parser_cls in ALL_PARSERS:
        registry.register(parser_cls())
