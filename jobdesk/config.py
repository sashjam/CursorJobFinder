"""Единственный модуль, который читает `.env`. Остальной код — только через функции ниже."""

from __future__ import annotations

import os
import re
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_LOADED = False


def env_file_path() -> Path:
    return _PROJECT_ROOT / ".env"


def ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = env_file_path()
    try:
        from dotenv import load_dotenv

        if env_path.is_file():
            load_dotenv(env_path, encoding="utf-8-sig", override=True)
    except ImportError:
        pass
    _ENV_LOADED = True


def reload_env() -> None:
    global _ENV_LOADED
    _ENV_LOADED = False
    ensure_env_loaded()


def _clean(value: str) -> str:
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    return v


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
    return "JobDesk/1.0 (your.email@example.com)"


def telegram_chat_id() -> str:
    return _get("BOT", "TELEGRAM_CHAT_ID", "CHAT_ID")


def telegram_bot_token() -> str:
    return _get("BOT_TOKEN", "TELEGRAM_BOT_TOKEN")


def telegram_bot_name() -> str:
    name = _get("BOT_NAME", "TELEGRAM_BOT_NAME")
    return name or "JobDesk"


def telegram_enabled() -> bool:
    return bool(telegram_bot_token() and telegram_chat_id())


def telegram_validate() -> tuple[bool, str]:
    """Проверка формата без вывода секретов."""
    token = telegram_bot_token()
    chat = telegram_chat_id()
    if not env_file_path().is_file():
        return False, f"Нет файла .env в {_PROJECT_ROOT}"
    if not token:
        return False, "Не задан BOT_TOKEN (токен от @BotFather)."
    if not chat:
        return False, "Не задан BOT — это числовой chat id, не имя бота."
    if chat.startswith("@"):
        return False, "BOT должен быть числом (chat id), а не @username. См. @userinfobot."
    if not re.fullmatch(r"-?\d+", chat):
        return False, "BOT (chat id) должен быть числом, например 123456789 или -1001234567890."
    if ":" not in token or len(token) < 20:
        return False, "BOT_TOKEN должен быть вида 1234567890:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    return True, "OK"


def telegram_status_label() -> str:
    ok, msg = telegram_validate()
    if ok:
        return f"Telegram: включён ({telegram_bot_name()})"
    if telegram_bot_token() or telegram_chat_id():
        return f"Telegram: {msg}"
    return f"Telegram: выключен — создайте .env (см. .env.example)"
