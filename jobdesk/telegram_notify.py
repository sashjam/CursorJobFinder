from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Callable

from jobdesk.config import telegram_bot_name, telegram_bot_token, telegram_chat_id, telegram_enabled
from jobdesk.models import Vacancy

_MAX_LINES = 15
_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_new_vacancies(
    items: list[Vacancy],
    *,
    on_result: Callable[[bool, str], None] | None = None,
) -> None:
    if not items:
        return
    if not telegram_enabled():
        if on_result:
            on_result(False, "Telegram не настроен (BOT + BOT_TOKEN в .env)")
        return
    text = _format_message(items)
    threading.Thread(
        target=_send_text,
        args=(text, on_result),
        daemon=True,
    ).start()


def send_test_message(*, on_result: Callable[[bool, str], None] | None = None) -> None:
    threading.Thread(
        target=_send_text,
        args=(
            f"{telegram_bot_name()}: тест JobDesk — уведомления работают.",
            on_result,
        ),
        daemon=True,
    ).start()


def _format_message(items: list[Vacancy]) -> str:
    bot = telegram_bot_name()
    lines = [f"{bot}: новые вакансии ({len(items)})", ""]
    for v in items[:_MAX_LINES]:
        company = v.company or "—"
        city = f" · {v.city}" if v.city else ""
        lines.append(f"• {v.title}{city}\n  {company}\n  {v.url}")
    if len(items) > _MAX_LINES:
        lines.append(f"\n… и ещё {len(items) - _MAX_LINES}")
    return "\n".join(lines)


def _send_text(text: str, on_result: Callable[[bool, str], None] | None = None) -> None:
    token = telegram_bot_token()
    chat_id = telegram_chat_id()
    if not token or not chat_id:
        if on_result:
            on_result(False, "Нет BOT_TOKEN или BOT (chat id)")
        return
    url = _API.format(token=token)
    ok, msg = _post_message(url, chat_id, text, html=False)
    if on_result:
        on_result(ok, msg)


def _post_message(url: str, chat_id: str, text: str, *, html: bool) -> tuple[bool, str]:
    body: dict[str, object] = {
        "chat_id": chat_id,
        "text": text[:4090],
        "disable_web_page_preview": True,
    }
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("ok"):
            return True, "Сообщение отправлено"
        return False, str(data.get("description", "ошибка Telegram API"))
    except urllib.error.HTTPError as exc:
        try:
            err = json.loads(exc.read().decode("utf-8"))
            desc = err.get("description", exc.reason)
        except (json.JSONDecodeError, UnicodeDecodeError):
            desc = str(exc)
        return False, desc
    except urllib.error.URLError as exc:
        return False, str(exc.reason)
