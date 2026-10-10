from __future__ import annotations

from collections.abc import Callable

from jobdesk.models import Vacancy
from jobdesk.telegram_notify import send_new_vacancies


def notify_after_fetch(
    new_items: list[Vacancy],
    *,
    total_unread: int,
    on_telegram_result: Callable[[bool, str], None] | None = None,
) -> None:
    """Уведомления после опроса: desktop + Telegram для подошедших вакансий."""
    if not new_items:
        return
    _notify_desktop(new_items, total_unread=total_unread)
    send_new_vacancies(new_items, on_result=on_telegram_result)


def _notify_desktop(new_items: list[Vacancy], *, total_unread: int) -> None:
    try:
        from plyer import notification
    except ImportError:
        return

    count_line = f"Непросмотренных всего: {total_unread}"
    if len(new_items) == 1:
        v = new_items[0]
        notification.notify(
            title="JobDesk · новая вакансия",
            message=f"{v.title}\n{v.company or '—'}\n{count_line}",
            app_name="JobDesk",
            timeout=10,
        )
        return

    notification.notify(
        title="JobDesk · новые вакансии",
        message=f"За этот опрос: {len(new_items)}\n{count_line}",
        app_name="JobDesk",
        timeout=10,
    )
