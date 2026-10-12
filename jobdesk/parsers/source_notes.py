"""Подсказки по полю «Запрос» и ограничения источников."""

from __future__ import annotations

SOURCE_QUERY_HINT: dict[str, str] = {
    "habr_rss": "Текст q, как на career.habr.com (например: python remote)",
    "habr_html": "Текст q для страницы вакансий",
    "hh_html": "Текст поиска, как на hh.ru",
    "hh_api": "Текст поиска; при ошибке API — автоматически HTML. JOBDESK_HH_USER_AGENT=App/1.0 (email)",
    "zarplata_html": "Текст поиска, как на zarplata.ru",
    "superjob_html": "Ключевые слова (keywords)",
    "rabota_html": "Строка query",
    "trudvsem_api": "Текст для opendata.trudvsem.ru",
    "geekjob_html": "Параметр q",
    "dou_html": "search — строка поиска",
    "dou_rss": "search или пусто (вся лента)",
    "devby_html": "search",
    "djini_html": "keywords",
    "remoteok_api": "Фильтр по словам в названии/компании (опционально)",
    "remotive_api": "search (англ.)",
    "jobicy_api": "tag (например python, devops)",
    "arbeitnow_api": "Локальный фильтр по запросу (опционально)",
    "himalayas_api": "search (англ., опционально)",
    "wwr_rss": "programming | devops | design | all или URL RSS",
    "rss_custom": "Полный URL RSS/Atom",
}

UNSUPPORTED_NOTE = """
Сайты без стабильного публичного API/RSS в этой версии:
Getmatch (SPA), LinkedIn, Indeed, Jooble (антибот), Хабр Q&A.
Их можно подключить через «Произвольный RSS», если найдёте ленту.
""".strip()
