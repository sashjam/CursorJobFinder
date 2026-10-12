from __future__ import annotations

import threading
import webbrowser
from datetime import datetime
from typing import Any

import customtkinter as ctk

from jobdesk.db import Database
from jobdesk.desired import derive_search_query
from jobdesk.engine import run_fetch
from jobdesk.app_badge import apply_badge
from jobdesk.config import ensure_env_loaded, env_file_path, reload_env, telegram_status_label, telegram_validate
from jobdesk.locations import CITY_OPTIONS, locations_to_json, parse_locations_json
from jobdesk.telegram_notify import send_test_message, send_test_vacancy
from jobdesk.notify import notify_after_fetch
from jobdesk.parsers.base import get_registry
from jobdesk.parsers.source_notes import SOURCE_QUERY_HINT, UNSUPPORTED_NOTE
from jobdesk.scheduler import PollScheduler


class JobDeskApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("JobDesk — поиск работы")
        self.geometry("980x640")
        self.minsize(820, 520)

        ensure_env_loaded()
        self.db = Database()

        self._fetch_lock = threading.Lock()
        self._status_var = ctk.StringVar(value="Готово")
        self._new_only_var = ctk.BooleanVar(value=True)
        self._city_vars: dict[str, ctk.BooleanVar] = {}

        self._build_ui()
        self._refresh_vacancy_list()
        self._refresh_subscriptions_list()

        self.scheduler = PollScheduler(
            interval_seconds=lambda: self.db.get_poll_interval_minutes() * 60,
            on_tick=lambda: self.after(0, self._run_fetch_async),
        )
        self.scheduler.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._update_badge()
        self.after(1500, self._run_fetch_async)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 4))

        tab_v = self.tabs.add("Вакансии")
        tab_w = self.tabs.add("Желаемая работа")
        tab_s = self.tabs.add("Подписки")
        tab_set = self.tabs.add("Настройки")
        tab_src = self.tabs.add("Источники")
        tab_help = self.tabs.add("Справка")

        self._build_vacancies_tab(tab_v)
        self._build_desired_tab(tab_w)
        self._build_subscriptions_tab(tab_s)
        self._build_settings_tab(tab_set)
        self._build_sources_tab(tab_src)
        self._build_help_tab(tab_help)

        status = ctk.CTkLabel(self, textvariable=self._status_var, anchor="w")
        status.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

    def _build_vacancies_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(
            toolbar,
            text="Обновить с сайтов",
            width=130,
            command=self._run_fetch_async,
        ).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(
            toolbar,
            text="Обновить список",
            width=130,
            fg_color="gray30",
            hover_color="gray25",
            command=self._refresh_list_only,
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkButton(
            toolbar, text="Отметить все просмотренными", command=self._mark_all_seen
        ).grid(row=0, column=2, padx=(0, 8))

        ctk.CTkCheckBox(
            toolbar,
            text="Только новые",
            variable=self._new_only_var,
            command=self._refresh_vacancy_list,
        ).grid(row=0, column=3, padx=(0, 8))

        self.lbl_new_count = ctk.CTkLabel(toolbar, text="")
        self.lbl_new_count.grid(row=0, column=4, sticky="w")

        self.vacancy_list = ctk.CTkScrollableFrame(parent)
        self.vacancy_list.grid(row=1, column=0, sticky="nsew")
        self.vacancy_list.grid_columnconfigure(0, weight=1)

    def _build_desired_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            parent,
            text="Опишите желаемую вакансию — текст сохраняется и используется при каждом опросе сайтов.",
            anchor="w",
            wraplength=720,
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

        self.desired_text = ctk.CTkTextbox(parent, height=180, wrap="word")
        self.desired_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        saved = self.db.get_desired_vacancy()
        if saved:
            self.desired_text.insert("1.0", saved)

        ctk.CTkLabel(
            parent,
            text="Города и регионы (можно несколько):",
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(4, 0))

        cities_box = ctk.CTkScrollableFrame(parent, height=130)
        cities_box.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        saved_locs = set(parse_locations_json(self.db.get_desired_locations()))
        if not saved_locs:
            saved_locs = {"Любая локация"}
        for i, city in enumerate(CITY_OPTIONS):
            var = ctk.BooleanVar(value=city in saved_locs)
            self._city_vars[city] = var
            ctk.CTkCheckBox(cities_box, text=city, variable=var).grid(
                row=i // 3, column=i % 3, sticky="w", padx=8, pady=2
            )

        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=4, column=0, sticky="ew", padx=8, pady=8)
        controls.grid_columnconfigure(1, weight=1)

        self.use_desired_var = ctk.BooleanVar(value=self.db.use_desired_vacancy_search())
        ctk.CTkCheckBox(
            controls,
            text="Искать по описанию (подставить запрос на сайтах)",
            variable=self.use_desired_var,
            command=self._toggle_use_desired,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.use_post_filter_var = ctk.BooleanVar(value=self.db.use_desired_post_filter())
        ctk.CTkCheckBox(
            controls,
            text="Доп. фильтр по ключевым словам описания (строже, может дать 0 результатов)",
            variable=self.use_post_filter_var,
            command=self._toggle_post_filter,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ctk.CTkButton(controls, text="Сохранить", width=120, command=self._save_desired).grid(
            row=2, column=0, padx=(0, 8)
        )
        ctk.CTkButton(
            controls,
            text="Сохранить и искать",
            width=160,
            command=self._save_desired_and_fetch,
        ).grid(row=2, column=1, sticky="w")

        self.desired_query_hint = ctk.CTkLabel(controls, text="", anchor="w", text_color="gray")
        self.desired_query_hint.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._update_desired_hint()

    def _update_desired_hint(self) -> None:
        text = self.desired_text.get("1.0", "end").strip() if hasattr(self, "desired_text") else ""
        q = derive_search_query(text) if text else ""
        lines: list[str] = []
        if q:
            lines.append(f"Запрос для сайтов: «{q}»")
        else:
            lines.append("Запрос для сайтов появится после текста описания.")
        updated = self.db.get_desired_vacancy_updated_at()
        if updated:
            lines.append(f"Последнее сохранение: {updated.strftime('%d.%m.%Y %H:%M')}")
        self.desired_query_hint.configure(text="\n".join(lines))

    def _collect_locations(self) -> list[str]:
        selected = [city for city, var in self._city_vars.items() if var.get()]
        if not selected:
            return ["Любая локация"]
        if "Любая локация" in selected and len(selected) > 1:
            selected = [c for c in selected if c != "Любая локация"]
        return selected or ["Любая локация"]

    def _save_desired(self) -> None:
        text = self.desired_text.get("1.0", "end").strip()
        self.db.set_desired_vacancy(text)
        self.db.set_use_desired_vacancy_search(self.use_desired_var.get())
        self.db.set_use_desired_post_filter(self.use_post_filter_var.get())
        self.db.set_desired_locations(locations_to_json(self._collect_locations()))
        self._update_desired_hint()
        self._status_var.set("Описание и города сохранены")

    def _save_desired_and_fetch(self) -> None:
        self._save_desired()
        self._run_fetch_async()

    def _toggle_use_desired(self) -> None:
        self.db.set_use_desired_vacancy_search(self.use_desired_var.get())

    def _toggle_post_filter(self) -> None:
        self.db.set_use_desired_post_filter(self.use_post_filter_var.get())

    def _build_subscriptions_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        form = ctk.CTkFrame(parent)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Название").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.sub_name = ctk.CTkEntry(form, placeholder_text="Python remote")
        self.sub_name.grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkLabel(form, text="Источник").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        sources = get_registry().list_sources()
        self.sub_source = ctk.CTkComboBox(
            form,
            values=[label for _, label in sources] or ["—"],
            width=420,
            command=self._on_source_changed,
        )
        self.sub_source.grid(row=1, column=1, sticky="ew", padx=8, pady=4)
        self._source_labels = {label: sid for sid, label in sources}
        self._label_to_source = {label: sid for sid, label in sources}
        if sources:
            self.sub_source.set(sources[0][1])

        ctk.CTkLabel(form, text="Запрос").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.sub_query = ctk.CTkEntry(form, placeholder_text="python django")
        self.sub_query.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        self.query_hint = ctk.CTkLabel(form, text="", anchor="w", text_color="gray", wraplength=520)
        self.query_hint.grid(row=3, column=1, sticky="w", padx=8, pady=(0, 4))
        self._on_source_changed(self.sub_source.get())

        ctk.CTkLabel(form, text="Исключить слова").grid(
            row=4, column=0, sticky="w", padx=8, pady=4
        )
        self.sub_exclude = ctk.CTkEntry(form, placeholder_text="1С, стажёр")
        self.sub_exclude.grid(row=4, column=1, sticky="ew", padx=8, pady=4)

        ctk.CTkButton(form, text="Добавить подписку", command=self._add_subscription).grid(
            row=5, column=1, sticky="e", padx=8, pady=8
        )

        self.subscriptions_list = ctk.CTkScrollableFrame(parent)
        self.subscriptions_list.grid(row=2, column=0, sticky="nsew")
        self.subscriptions_list.grid_columnconfigure(0, weight=1)

    def _build_settings_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="Интервал проверки (мин)").grid(
            row=0, column=0, sticky="w", padx=8, pady=12
        )
        self.poll_spin = ctk.CTkEntry(parent, width=80)
        self.poll_spin.insert(0, str(self.db.get_poll_interval_minutes()))
        self.poll_spin.grid(row=0, column=1, sticky="w", padx=8, pady=12)

        ctk.CTkButton(parent, text="Сохранить", command=self._save_settings).grid(
            row=1, column=1, sticky="w", padx=8, pady=4
        )

        self.telegram_status = ctk.CTkLabel(parent, text=telegram_status_label(), anchor="w")
        self.telegram_status.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(12, 4))

        tg_btns = ctk.CTkFrame(parent, fg_color="transparent")
        tg_btns.grid(row=3, column=0, columnspan=2, sticky="w", padx=8)
        ctk.CTkButton(tg_btns, text="Тест Telegram", width=120, command=self._test_telegram).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            tg_btns,
            text="Тест: вакансия в Telegram",
            width=200,
            command=self._test_telegram_vacancy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            tg_btns,
            text="Перечитать .env",
            width=130,
            fg_color="gray30",
            command=self._reload_env_ui,
        ).pack(side="left")

        ctk.CTkLabel(
            parent,
            text=(
                f"Файл: {env_file_path()}\n"
                "BOT — числовой chat id · BOT_TOKEN — от @BotFather · BOT_NAME — подпись в сообщениях\n"
                "После правки .env нажмите «Перечитать .env». Формат — вкладка «Справка» или .env.example"
            ),
            justify="left",
            wraplength=720,
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=8)

    def _build_help_tab(self, parent: ctk.CTkFrame) -> None:
        from pathlib import Path

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        guide_path = Path(__file__).resolve().parents[2] / "docs" / "USER_GUIDE.md"
        text = guide_path.read_text(encoding="utf-8") if guide_path.is_file() else "Файл docs/USER_GUIDE.md не найден."
        box = ctk.CTkTextbox(parent, wrap="word")
        box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _build_sources_tab(self, parent: ctk.CTkFrame) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        box = ctk.CTkScrollableFrame(parent)
        box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        box.grid_columnconfigure(0, weight=1)
        registry = get_registry()
        for i, (sid, label) in enumerate(registry.list_sources()):
            hint = SOURCE_QUERY_HINT.get(sid, "Поисковый запрос сайта")
            ctk.CTkLabel(
                box,
                text=f"{label}\n  → {hint}",
                anchor="w",
                justify="left",
            ).grid(row=i, column=0, sticky="ew", pady=2)
        ctk.CTkLabel(box, text="\n" + UNSUPPORTED_NOTE, anchor="w", justify="left", wraplength=700).grid(
            row=999, column=0, sticky="w", pady=12
        )

    def _on_source_changed(self, choice: str) -> None:
        sid = self._label_to_source.get(choice, "")
        hint = SOURCE_QUERY_HINT.get(sid, "Текст поиска или URL — см. вкладку «Источники»")
        self.query_hint.configure(text=hint)

    def _run_fetch_async(self) -> None:
        if not self._fetch_lock.acquire(blocking=False):
            return
        self._status_var.set("Обновление…")

        def work() -> None:
            try:
                result = run_fetch(self.db)
                self.after(0, lambda r=result: self._on_fetch_done(r))
            finally:
                self._fetch_lock.release()

        threading.Thread(target=work, daemon=True).start()

    def _on_fetch_done(self, result) -> None:
        self._refresh_vacancy_list()
        self._refresh_subscriptions_list()
        total_unread = self.db.count_new()
        self._update_badge()
        parts: list[str] = []
        if result.raw_total:
            parts.append(f"с сайтов: {result.raw_total}")
        if result.kept_total:
            parts.append(f"подошло: {result.kept_total}")
        if result.new_vacancies:
            parts.append(f"новых в базе: {len(result.new_vacancies)}")
        if result.errors:
            self._status_var.set("; ".join(result.errors[:2]))
        elif result.new_vacancies:
            self._status_var.set(" · ".join(parts))
            notify_after_fetch(
                result.new_vacancies,
                total_unread=total_unread,
                on_telegram_result=lambda ok, msg: self.after(
                    0, lambda: self._telegram_feedback(ok, msg)
                ),
            )
        elif parts:
            self._status_var.set(" · ".join(parts) + " — см. подсказки выше")
        else:
            self._status_var.set("Нет данных с сайтов")

    def _telegram_feedback(self, ok: bool, msg: str) -> None:
        if ok:
            return
        self._status_var.set(f"Telegram: {msg}")

    def _test_telegram(self) -> None:
        ok, hint = telegram_validate()
        if not ok:
            self._status_var.set(f"Telegram: {hint}")
            return
        self._status_var.set("Отправка теста в Telegram…")
        send_test_message(
            on_result=lambda o, m: self.after(0, lambda: self._telegram_test_done(o, m))
        )

    def _test_telegram_vacancy(self) -> None:
        ok, hint = telegram_validate()
        if not ok:
            self._status_var.set(f"Telegram: {hint}")
            return
        self._status_var.set("Отправка тестовой вакансии в Telegram…")
        send_test_vacancy(
            on_result=lambda o, m: self.after(0, lambda: self._telegram_test_done(o, m))
        )

    def _telegram_test_done(self, ok: bool, msg: str) -> None:
        reload_env()
        self.telegram_status.configure(text=telegram_status_label())
        if ok:
            self._status_var.set(f"Telegram: успех — {msg}")
        else:
            _, hint = telegram_validate()
            extra = f" ({hint})" if hint != "OK" else ""
            self._status_var.set(f"Telegram: {msg}{extra}")

    def _reload_env_ui(self) -> None:
        reload_env()
        self.telegram_status.configure(text=telegram_status_label())
        self._status_var.set("Переменные окружения перечитаны")

    def _refresh_list_only(self) -> None:
        self._refresh_vacancy_list()
        self._status_var.set("Список обновлён")

    def _refresh_vacancy_list(self) -> None:
        for w in self.vacancy_list.winfo_children():
            w.destroy()

        locs = parse_locations_json(self.db.get_desired_locations())
        rows = self.db.list_vacancies(
            new_only=self._new_only_var.get(),
            location_filter=locs if locs and "Любая локация" not in locs else None,
        )
        new_count = self.db.count_new()
        self.lbl_new_count.configure(text=f"Непросмотренных: {new_count}")
        self._update_badge()

        if not rows:
            ctk.CTkLabel(
                self.vacancy_list,
                text="Вакансий пока нет. Нажмите «Обновить» или добавьте подписку.",
            ).grid(row=0, column=0, sticky="w", pady=8)
            return

        for i, row in enumerate(rows):
            self._vacancy_row(i, row)

    def _vacancy_row(self, index: int, row: dict[str, Any]) -> None:
        is_new = bool(row["is_new"])
        frame = ctk.CTkFrame(self.vacancy_list)
        frame.grid(row=index, column=0, sticky="ew", pady=4)
        frame.grid_columnconfigure(1, weight=1)

        icon = "🆕" if is_new else "✓"
        icon_tip = "Новая" if is_new else "Просмотрена"
        title_color = ("#1f538d", "#7eb8ff") if is_new else ("gray35", "gray60")

        ctk.CTkLabel(
            frame,
            text=icon,
            width=36,
            font=ctk.CTkFont(size=18),
        ).grid(row=0, column=0, rowspan=2, padx=(8, 0), pady=8)

        title = row["title"]
        meta_parts = [
            icon_tip,
            row.get("city") or None,
            row["company"] or None,
            _format_dt(row.get("published_at") or row.get("first_seen_at")),
            row["source"],
        ]
        meta = " · ".join(p for p in meta_parts if p)

        ctk.CTkLabel(
            frame,
            text=title,
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
            text_color=title_color,
            wraplength=620,
        ).grid(row=0, column=1, sticky="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(frame, text=meta, anchor="w", text_color="gray").grid(
            row=1, column=1, sticky="w", padx=10, pady=(0, 8)
        )

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=2, padx=8, pady=8)

        ctk.CTkButton(
            btns,
            text="Открыть",
            width=80,
            command=lambda u=row["url"]: webbrowser.open(u),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btns,
            text="Прочитано",
            width=90,
            fg_color="gray30" if is_new else "gray20",
            state="normal" if is_new else "disabled",
            command=lambda vid=row["id"]: self._mark_seen(vid),
        ).pack(side="left", padx=4)

    def _mark_seen(self, vacancy_id: int) -> None:
        self.db.mark_seen(vacancy_id)
        self._refresh_vacancy_list()

    def _mark_all_seen(self) -> None:
        self.db.mark_all_seen()
        self._refresh_vacancy_list()

    def _refresh_subscriptions_list(self) -> None:
        for w in self.subscriptions_list.winfo_children():
            w.destroy()

        subs = self.db.list_subscriptions()
        registry = get_registry()
        id_to_label = {sid: label for sid, label in registry.list_sources()}

        for i, sub in enumerate(subs):
            frame = ctk.CTkFrame(self.subscriptions_list)
            frame.grid(row=i, column=0, sticky="ew", pady=4)
            frame.grid_columnconfigure(0, weight=1)

            src_label = id_to_label.get(sub.source, sub.source)
            checked = "вкл" if sub.enabled else "выкл"
            last = (
                sub.last_checked_at.strftime("%d.%m %H:%M")
                if sub.last_checked_at
                else "ещё не проверялась"
            )
            text = f"{sub.name} — {src_label}\nЗапрос: «{sub.query or '—'}» · {checked} · {last}"
            ctk.CTkLabel(frame, text=text, anchor="w", justify="left").grid(
                row=0, column=0, sticky="w", padx=10, pady=8
            )

            btns = ctk.CTkFrame(frame, fg_color="transparent")
            btns.grid(row=0, column=1, padx=8)

            ctk.CTkButton(
                btns,
                text="Вкл/выкл",
                width=70,
                command=lambda sid=sub.id, en=sub.enabled: self._toggle_sub(sid, en),
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                btns,
                text="Сейчас",
                width=60,
                command=lambda sid=sub.id: self._fetch_one(sid),
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                btns,
                text="Удалить",
                width=70,
                fg_color="#8b0000",
                hover_color="#a40000",
                command=lambda sid=sub.id: self._delete_sub(sid),
            ).pack(side="left", padx=2)

    def _add_subscription(self) -> None:
        name = self.sub_name.get().strip()
        if not name:
            self._status_var.set("Укажите название подписки")
            return
        label = self.sub_source.get()
        source = self._source_labels.get(label, "habr_rss")
        self.db.add_subscription(
            name=name,
            source=source,
            query=self.sub_query.get().strip(),
            exclude_words=self.sub_exclude.get().strip(),
        )
        self.sub_name.delete(0, "end")
        self.sub_query.delete(0, "end")
        self.sub_exclude.delete(0, "end")
        self._refresh_subscriptions_list()
        self._status_var.set("Подписка добавлена")
        self._run_fetch_async()

    def _toggle_sub(self, sub_id: int, currently_enabled: bool) -> None:
        self.db.update_subscription_enabled(sub_id, not currently_enabled)
        self._refresh_subscriptions_list()

    def _delete_sub(self, sub_id: int) -> None:
        self.db.delete_subscription(sub_id)
        self._refresh_subscriptions_list()

    def _fetch_one(self, sub_id: int) -> None:
        if not self._fetch_lock.acquire(blocking=False):
            return
        self._status_var.set("Обновление подписки…")

        def work() -> None:
            try:
                result = run_fetch(self.db, subscription_ids=[sub_id])
                self.after(0, lambda r=result: self._on_fetch_done(r))
            finally:
                self._fetch_lock.release()

        threading.Thread(target=work, daemon=True).start()

    def _save_settings(self) -> None:
        try:
            minutes = int(self.poll_spin.get().strip())
        except ValueError:
            self._status_var.set("Интервал должен быть числом")
            return
        self.db.set_poll_interval_minutes(minutes)
        self.scheduler.reschedule()
        self._status_var.set(f"Интервал: {minutes} мин")

    def _update_badge(self) -> None:
        apply_badge(self, self.db.count_new())

    def _on_close(self) -> None:
        self.scheduler.stop()
        self.destroy()


def _format_dt(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value[:16]


def run_app() -> None:
    app = JobDeskApp()
    app.mainloop()
