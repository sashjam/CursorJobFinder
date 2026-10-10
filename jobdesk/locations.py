from __future__ import annotations

import json
import re

from jobdesk.models import Vacancy

# Города/регионы для выбора на вкладке «Желаемая работа»
CITY_OPTIONS: list[str] = [
    "Любая локация",
    "Удалённо",
    "Москва",
    "Московская область",
    "Санкт-Петербург",
    "Ленинградская область",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Краснодар",
    "Ростов-на-Дону",
    "Самара",
    "Уфа",
    "Воронеж",
    "Киев",
    "Минск",
]

_REMOTE_MARKERS = (
    "удален",
    "удалён",
    "remote",
    "дистанцион",
    " anywhere",
    " home office",
)


def parse_locations_json(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except json.JSONDecodeError:
            pass
    return [p.strip() for p in re.split(r"[,;\n]+", raw) if p.strip()]


def locations_to_json(items: list[str]) -> str:
    return json.dumps(items, ensure_ascii=False)


def extract_city_from_text(*parts: str) -> str:
    text = " ".join(p for p in parts if p).strip()
    if not text:
        return ""
    low = text.lower()
    if any(m in low for m in _REMOTE_MARKERS):
        return "Удалённо"
    m = re.search(r"\(([^()]{2,48})\)\s*$", text)
    if m:
        return m.group(1).strip()
    m = re.search(
        r"(?:город|локация|офис)[:\s]+([А-ЯA-Z][а-яa-zA-Z\s-]{2,30})",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return ""


def _vacancy_hay(v: Vacancy) -> str:
    return f"{v.title} {v.company} {v.description} {v.city}".lower()


def matches_locations(v: Vacancy, selected: list[str]) -> bool:
    if not selected or "Любая локация" in selected:
        return True
    hay = _vacancy_hay(v)
    city = (v.city or "").lower()

    for loc in selected:
        key = loc.lower().strip()
        if not key:
            continue
        if key in ("удалённо", "удаленно", "remote"):
            if "удалённо" in city or any(m in hay for m in _REMOTE_MARKERS):
                return True
            continue
        if key in hay or key in city:
            return True
        # Москва ⊆ Московская область не смешиваем — точное вхождение подстроки
    return False
