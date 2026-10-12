"""Fetch vacancies via Python parsers (stdin JSON config → stdout JSON result)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_root = str(_PROJECT_ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)

_REQUIRED = (
    ("certifi", "certifi"),
    ("feedparser", "feedparser"),
    ("bs4", "beautifulsoup4"),
    ("dotenv", "python-dotenv"),
)


def _missing_packages() -> list[str]:
    missing: list[str] = []
    for module, pip_name in _REQUIRED:
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)
    return missing


def _fail(errors: list[str]) -> None:
    payload: dict[str, Any] = {
        "ok": False,
        "errors": errors,
        "checked_subscriptions": 0,
        "raw_total": 0,
        "kept_total": 0,
        "new_count": 0,
        "vacancies": [],
    }
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.exit(0)


def _apply_settings(db: Any, settings: dict) -> None:
    if "desired_vacancy" in settings:
        db.set_desired_vacancy(str(settings.get("desired_vacancy") or ""))
    if "use_desired_vacancy_search" in settings:
        db.set_use_desired_vacancy_search(bool(settings["use_desired_vacancy_search"]))
    if "use_desired_post_filter" in settings:
        db.set_use_desired_post_filter(bool(settings["use_desired_post_filter"]))
    if "desired_locations" in settings:
        raw = settings["desired_locations"]
        if isinstance(raw, list):
            db.set_desired_locations(json.dumps(raw, ensure_ascii=False))
        else:
            db.set_desired_locations(str(raw or "[]"))


def run_from_config(config: dict) -> dict:
    missing = _missing_packages()
    if missing:
        return {
            "ok": False,
            "errors": [
                "Не установлены Python-зависимости: "
                + ", ".join(missing)
                + f". Выполните в корне проекта: pip install -r requirements.txt "
                f"(интерпретатор: {sys.executable})"
            ],
            "checked_subscriptions": 0,
            "raw_total": 0,
            "kept_total": 0,
            "new_count": 0,
            "vacancies": [],
        }

    try:
        from jobdesk.config import ensure_env_loaded
        from jobdesk.db import Database
        from jobdesk.engine import run_fetch
    except ImportError as exc:
        return {
            "ok": False,
            "errors": [
                f"Ошибка импорта JobDesk ({exc}). "
                f"Проверьте pip install -r requirements.txt для {sys.executable}"
            ],
            "checked_subscriptions": 0,
            "raw_total": 0,
            "kept_total": 0,
            "new_count": 0,
            "vacancies": [],
        }

    ensure_env_loaded()
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        db = Database(path=path)
        for sub in config.get("subscriptions", []):
            sid = db.add_subscription(
                str(sub.get("name") or "Подписка"),
                str(sub.get("source") or "habr_rss"),
                str(sub.get("query") or ""),
                str(sub.get("exclude_words") or ""),
            )
            if not sub.get("enabled", True):
                db.update_subscription_enabled(sid, False)

        _apply_settings(db, config.get("settings") or {})

        result = run_fetch(db)
        with db._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, dedupe_key, external_id, source, subscription_id,
                       title, company, url, description, city,
                       published_at, first_seen_at, is_new
                FROM vacancies
                ORDER BY COALESCE(published_at, first_seen_at) DESC
                LIMIT 5000
                """
            ).fetchall()
        vacancies = [dict(r) for r in rows]

        return {
            "ok": True,
            "errors": result.errors,
            "checked_subscriptions": result.checked_subscriptions,
            "raw_total": result.raw_total,
            "kept_total": result.kept_total,
            "new_count": len(result.new_vacancies),
            "vacancies": vacancies,
        }
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        config = json.load(sys.stdin)
    except json.JSONDecodeError:
        _fail(["Некорректный JSON конфигурации"])
        return

    out = run_from_config(config)
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        _fail([f"{type(exc).__name__}: {exc}"])
