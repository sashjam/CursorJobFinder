from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from jobdesk.models import Subscription, Vacancy
from jobdesk.paths import database_path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or database_path()
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    query TEXT NOT NULL DEFAULT '',
                    exclude_words TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    last_checked_at TEXT
                );

                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedupe_key TEXT NOT NULL UNIQUE,
                    external_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    subscription_id INTEGER,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL DEFAULT '',
                    url TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    published_at TEXT,
                    first_seen_at TEXT NOT NULL,
                    is_new INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_vacancies_first_seen
                    ON vacancies(first_seen_at DESC);
                CREATE INDEX IF NOT EXISTS idx_vacancies_is_new
                    ON vacancies(is_new);
                """
            )
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'poll_interval_minutes'"
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    ("poll_interval_minutes", "15"),
                )
            cols = {r[1] for r in conn.execute("PRAGMA table_info(vacancies)")}
            if "city" not in cols:
                conn.execute(
                    "ALTER TABLE vacancies ADD COLUMN city TEXT NOT NULL DEFAULT ''"
                )

    def get_poll_interval_minutes(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'poll_interval_minutes'"
            ).fetchone()
        try:
            return max(1, int(row["value"]))
        except (TypeError, ValueError):
            return 15

    def set_poll_interval_minutes(self, minutes: int) -> None:
        minutes = max(1, min(24 * 60, minutes))
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("poll_interval_minutes", str(minutes)),
            )

    def _get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return default
        return row["value"] if row["value"] is not None else default

    def _set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_desired_vacancy(self) -> str:
        return self._get_setting("desired_vacancy", "")

    def set_desired_vacancy(self, text: str) -> None:
        self._set_setting("desired_vacancy", text)
        self._set_setting("desired_vacancy_updated_at", _utc_now_iso())

    def get_desired_vacancy_updated_at(self) -> datetime | None:
        return _parse_dt(self._get_setting("desired_vacancy_updated_at"))

    def use_desired_vacancy_search(self) -> bool:
        return self._get_setting("use_desired_vacancy_search", "1") != "0"

    def set_use_desired_vacancy_search(self, enabled: bool) -> None:
        self._set_setting("use_desired_vacancy_search", "1" if enabled else "0")

    def use_desired_post_filter(self) -> bool:
        return self._get_setting("use_desired_post_filter", "0") == "1"

    def set_use_desired_post_filter(self, enabled: bool) -> None:
        self._set_setting("use_desired_post_filter", "1" if enabled else "0")

    def get_desired_locations(self) -> str:
        return self._get_setting("desired_locations", "[]")

    def set_desired_locations(self, json_list: str) -> None:
        self._set_setting("desired_locations", json_list)

    def list_subscriptions(self) -> list[Subscription]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, source, query, exclude_words, enabled, last_checked_at
                FROM subscriptions
                ORDER BY id
                """
            ).fetchall()
        return [_row_to_subscription(r) for r in rows]

    def add_subscription(
        self,
        name: str,
        source: str,
        query: str,
        exclude_words: str = "",
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO subscriptions (name, source, query, exclude_words, enabled)
                VALUES (?, ?, ?, ?, 1)
                """,
                (name.strip(), source, query.strip(), exclude_words.strip()),
            )
            return int(cur.lastrowid)

    def update_subscription_enabled(self, sub_id: int, enabled: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE subscriptions SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, sub_id),
            )

    def delete_subscription(self, sub_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))

    def touch_subscription_checked(self, sub_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE subscriptions SET last_checked_at = ? WHERE id = ?",
                (_utc_now_iso(), sub_id),
            )

    def upsert_vacancies(self, items: list[Vacancy]) -> list[Vacancy]:
        """Insert new vacancies; return list of newly inserted ones."""
        if not items:
            return []
        now = _utc_now_iso()
        new_items: list[Vacancy] = []
        with self._connect() as conn:
            for v in items:
                pub = v.published_at.isoformat() if v.published_at else None
                try:
                    conn.execute(
                        """
                        INSERT INTO vacancies (
                            dedupe_key, external_id, source, subscription_id,
                            title, company, url, description, city, published_at,
                            first_seen_at, is_new
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            v.dedupe_key,
                            v.external_id,
                            v.source,
                            v.subscription_id,
                            v.title,
                            v.company,
                            v.url,
                            v.description,
                            v.city or "",
                            pub,
                            now,
                        ),
                    )
                    new_items.append(v)
                except sqlite3.IntegrityError:
                    conn.execute(
                        """
                        UPDATE vacancies SET
                            title = ?, company = ?, url = ?, description = ?,
                            city = CASE WHEN ? != '' THEN ? ELSE city END,
                            published_at = COALESCE(?, published_at)
                        WHERE dedupe_key = ?
                        """,
                        (
                            v.title,
                            v.company,
                            v.url,
                            v.description,
                            v.city or "",
                            v.city or "",
                            pub,
                            v.dedupe_key,
                        ),
                    )
        return new_items

    def list_vacancies(
        self,
        *,
        new_only: bool = False,
        limit: int = 500,
        location_filter: list[str] | None = None,
    ) -> list[dict]:
        from jobdesk.locations import matches_locations
        from jobdesk.models import Vacancy

        sql = """
            SELECT id, title, company, url, source, city, published_at, first_seen_at, is_new
            FROM vacancies
        """
        params: list[object] = []
        if new_only:
            sql += " WHERE is_new = 1"
        sql += " ORDER BY COALESCE(published_at, first_seen_at) DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        items = [dict(r) for r in rows]
        if not location_filter:
            return items
        out: list[dict] = []
        for row in items:
            v = Vacancy(
                external_id=str(row["id"]),
                source=row["source"],
                title=row["title"],
                company=row.get("company") or "",
                url=row["url"],
                description="",
                city=row.get("city") or "",
                published_at=None,
            )
            if matches_locations(v, location_filter):
                out.append(row)
        return out

    def mark_all_seen(self) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE vacancies SET is_new = 0 WHERE is_new = 1")

    def mark_seen(self, vacancy_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE vacancies SET is_new = 0 WHERE id = ?", (vacancy_id,)
            )

    def count_new(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM vacancies WHERE is_new = 1"
            ).fetchone()
        return int(row["c"])


def _row_to_subscription(row: sqlite3.Row) -> Subscription:
    return Subscription(
        id=int(row["id"]),
        name=row["name"],
        source=row["source"],
        query=row["query"],
        exclude_words=row["exclude_words"],
        enabled=bool(row["enabled"]),
        last_checked_at=_parse_dt(row["last_checked_at"]),
    )
