"""Единственный модуль, который читает `.env`. Остальной код — только через функции ниже."""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_LOADED = False


def ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = _PROJECT_ROOT / ".env"
    try:
        from dotenv import load_dotenv

        if env_path.is_file():
            load_dotenv(env_path, encoding="utf-8")
    except ImportError:
        pass
    _ENV_LOADED = True


def reload_env() -> None:
    global _ENV_LOADED
    _ENV_LOADED = False
    ensure_env_loaded()


def _clean(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _get(*names: str) -> str:
    ensure_env_loaded()
    for name in names:
        raw = os.environ.get(name)
        if raw is not None and str(raw).strip():
            return _clean(str(raw))
    return ""


def hh_user_agent() -> str:
    custom = _get("JOBDESK_HH_USER_AGENT")
    if custom:
        return custom
    return "JobDesk/1.0 (mailto:jobdesk@example.com)"


def telegram_chat_id() -> str:
    return _get("BOT", "TELEGRAM_CHAT_ID", "CHAT_ID")


def telegram_bot_token() -> str:
    return _get("BOT_TOKEN", "TELEGRAM_BOT_TOKEN")


def telegram_bot_name() -> str:
    name = _get("BOT_NAME", "TELEGRAM_BOT_NAME")
    return name or "JobDesk"


def telegram_enabled() -> bool:
    return bool(telegram_bot_token() and telegram_chat_id())


def telegram_status_label() -> str:
    if telegram_enabled():
        name = telegram_bot_name()
        return f"Telegram: включён ({name})"
    if telegram_bot_token() or telegram_chat_id():
        missing = []
        if not telegram_bot_token():
            missing.append("BOT_TOKEN")
        if not telegram_chat_id():
            missing.append("BOT (chat id)")
        return f"Telegram: не хватает {', '.join(missing)}"
    return "Telegram: выключен (.env в корне проекта)"
