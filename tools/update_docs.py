"""Синхронизация документации с реестром парсеров (register.py + source_notes.py)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jobdesk import __version__
from jobdesk.parsers.base import get_registry
from jobdesk.parsers.source_notes import SOURCE_QUERY_HINT, UNSUPPORTED_NOTE

DOCS = ROOT / "docs" / "JobDesk.md"
README = ROOT / "README.md"

START = "<!-- jobdesk:sources:auto -->"
END = "<!-- /jobdesk:sources:auto -->"


def _region(label: str, source_id: str) -> str:
    if label.startswith("🇷🇺"):
        return "Россия"
    if label.startswith("🇺🇦"):
        return "Украина"
    if label.startswith("🇧🇾"):
        return "Беларусь"
    if label.startswith("🌍"):
        return "Удалённая работа / международные API"
    if source_id == "rss_custom" or label.startswith("📡"):
        return "Универсальный"
    return "Прочее"


def build_sources_markdown() -> str:
    registry = get_registry()
    rows = registry.list_sources()
    count = len(rows)

    by_region: dict[str, list[tuple[str, str, str]]] = {}
    for sid, label in rows:
        region = _region(label, sid)
        hint = SOURCE_QUERY_HINT.get(sid, "Поисковый запрос сайта")
        by_region.setdefault(region, []).append((sid, label, hint))

    order = [
        "Россия",
        "Украина",
        "Беларусь",
        "Удалённая работа / международные API",
        "Универсальный",
        "Прочее",
    ]
    lines = [
        f"Всего **{count}** встроенных парсеров (обновлено скриптом `tools/update_docs.py`).",
        "",
        "Внутренний ID (`source_id`) сохраняется в базе в поле `source`.",
        "",
    ]
    for region in order:
        items = by_region.get(region)
        if not items:
            continue
        lines.append(f"### {region}")
        lines.append("")
        lines.append("| ID | Название в UI | Поле «Запрос» |")
        lines.append("|----|---------------|---------------|")
        for sid, label, hint in items:
            safe_hint = hint.replace("|", "\\|")
            lines.append(f"| `{sid}` | {label} | {safe_hint} |")
        lines.append("")

    lines.extend(
        [
            "### Без встроенного парсера",
            "",
            UNSUPPORTED_NOTE.replace("\n", "\n\n"),
            "",
        ]
    )
    return "\n".join(lines)


def patch_file(path: Path, start: str, end: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{body}\n{end}"
    if not pattern.search(text):
        raise SystemExit(f"Маркеры {start} не найдены в {path}")
    path.write_text(pattern.sub(replacement, text, count=1), encoding="utf-8")


def patch_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\*\*Версия приложения:\*\* \d+\.\d+\.\d+",
        f"**Версия приложения:** {__version__}",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8")


def patch_readme_count(count: int) -> None:
    text = README.read_text(encoding="utf-8")
    text = re.sub(
        r"## Подключённые источники \(\d+\)",
        f"## Подключённые источники ({count})",
        text,
        count=1,
    )
    README.write_text(text, encoding="utf-8")


def main() -> None:
    body = build_sources_markdown()
    patch_file(DOCS, START, END, body)
    patch_version(DOCS)
    patch_readme_count(len(get_registry().list_sources()))
    print(f"OK: docs synced, {len(get_registry().list_sources())} sources, version {__version__}")


if __name__ == "__main__":
    main()
