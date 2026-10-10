from __future__ import annotations

import re

from jobdesk.models import Vacancy

_STOPWORDS = frozenset(
    """
    и в во не на с со к у о из за для при по от до об про без при
    a an the or and to of in on for with web
    """.split()
)

# Поиск в тексте вакансии: синонимы для стека
_MATCH_ALIASES: dict[str, tuple[str, ...]] = {
    "js": ("js", "javascript", "node", "nodejs"),
    "vue": ("vue", "vue.js", "vuejs"),
    "mysql": ("mysql", "mariadb", "sql"),
    "html5": ("html5", "html"),
    "php": ("php",),
    "fullstack": ("fullstack", "full-stack", "full stack"),
}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        key = x.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(x)
    return out


def extract_keywords(description: str, *, limit: int = 14) -> list[str]:
    """Ключевые слова из описания (скобки, запятые, текст)."""
    tokens: list[str] = []
    for inner in re.findall(r"\(([^)]+)\)", description):
        for part in re.split(r"[,;/|+]+", inner):
            part = part.strip()
            if len(part) >= 2:
                tokens.append(part)

    body = re.sub(r"\([^)]*\)", " ", description)
    for t in re.findall(r"[a-zA-Z#+][\w+#.-]*|[а-яА-ЯёЁ]{3,}", body):
        low = t.lower()
        if low in _STOPWORDS or t.isdigit():
            continue
        tokens.append(t)

    return _dedupe(tokens)[:limit]


def derive_search_query(description: str, *, max_len: int = 120) -> str:
    """Запрос для сайтов: приоритет — технологии из скобок и ключевые слова."""
    keywords = extract_keywords(description)
    if keywords:
        # Стек + роль (fullstack и т.д.), без скобок и запятых
        q = " ".join(keywords[:4])
        return q[:max_len].strip()

    text = " ".join(description.split())
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0]
    return text.strip()


def significant_words(description: str, *, limit: int = 14) -> list[str]:
    words = [w.lower() for w in extract_keywords(description, limit=limit)]
    return words[:limit]


def _keyword_hits(hay: str, word: str) -> bool:
    w = word.lower()
    variants = _MATCH_ALIASES.get(w, (w,))
    return any(v in hay for v in variants)


def matches_desired(v: Vacancy, description: str) -> bool:
    """Достаточно одного совпадения по любому ключевому слову из описания."""
    words = significant_words(description)
    if not words:
        return True
    hay = f"{v.title} {v.company} {v.description}".lower()
    return any(_keyword_hits(hay, w) for w in words)
