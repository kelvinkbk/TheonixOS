"""
Theonix Browser — History Manager.
Handles persistent SQLite storage for visited URLs, timestamps, titles, and visit counts.
"""

import os
import sqlite3
import time
from typing import List, Dict, Any

HISTORY_DB_PATH = os.path.expanduser("~/.config/theonix/browser/history.db")


class HistoryManager:
    def __init__(self, db_path: str = HISTORY_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    title TEXT,
                    visit_count INTEGER DEFAULT 1,
                    last_visited INTEGER
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_last_visited ON history(last_visited DESC)")

    def add_entry(self, url: str, title: str):
        if not url or url.startswith("theonix://") or url.startswith("about:"):
            return
        now = int(time.time())
        clean_title = title.strip() if title else url
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO history (url, title, visit_count, last_visited)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    visit_count = visit_count + 1,
                    last_visited = excluded.last_visited
            """, (url, clean_title, now))

    def get_recent(self, limit: int = 50, search_query: str = "") -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if search_query:
                q = f"%{search_query}%"
                cur = conn.execute(
                    "SELECT id, url, title, visit_count, last_visited FROM history WHERE title LIKE ? OR url LIKE ? ORDER BY last_visited DESC LIMIT ?",
                    (q, q, limit)
                )
            else:
                cur = conn.execute(
                    "SELECT id, url, title, visit_count, last_visited FROM history ORDER BY last_visited DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cur.fetchall()]

    def delete_entry(self, entry_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))

    def clear_all(self):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM history")
