"""
Theonix Browser — Bookmarks Manager.
Handles persistent SQLite storage for bookmark links, folders, and quick-access items.
"""

import os
import sqlite3
import time
from typing import List, Dict, Any

BOOKMARKS_DB_PATH = os.path.expanduser("~/.config/theonix/browser/bookmarks.db")

DEFAULT_BOOKMARKS = [
    ("⚡ Theonix OS", "https://theonixos.xyz", "Official Website & Docs"),
    ("📖 Arch Wiki", "https://wiki.archlinux.org", "Arch Linux Reference"),
    ("🟣 Flathub", "https://flathub.org", "Linux Flatpak App Store"),
    ("🐙 GitHub", "https://github.com/kelvinkbk/TheonixOS", "Theonix Project Code"),
    ("🔍 DuckDuckGo", "https://duckduckgo.com", "Privacy Search Engine"),
]


class BookmarksManager:
    def __init__(self, db_path: str = BOOKMARKS_DB_PATH):
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
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    folder TEXT DEFAULT 'default',
                    created_at INTEGER
                )
            """)
            # Seed defaults if empty
            cur = conn.execute("SELECT COUNT(*) as count FROM bookmarks")
            if cur.fetchone()["count"] == 0:
                now = int(time.time())
                for title, url, _ in DEFAULT_BOOKMARKS:
                    conn.execute(
                        "INSERT OR IGNORE INTO bookmarks (title, url, folder, created_at) VALUES (?, ?, 'default', ?)",
                        (title, url, now)
                    )

    def add_bookmark(self, title: str, url: str, folder: str = "default") -> bool:
        if not url:
            return False
        clean_title = title.strip() if title else url
        now = int(time.time())
        try:
            with self._get_conn() as conn:
                conn.execute(
                    "INSERT INTO bookmarks (title, url, folder, created_at) VALUES (?, ?, ?, ?)",
                    (clean_title, url, folder, now)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_bookmark(self, url: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM bookmarks WHERE url = ?", (url,))

    def is_bookmarked(self, url: str) -> bool:
        if not url:
            return False
        with self._get_conn() as conn:
            cur = conn.execute("SELECT id FROM bookmarks WHERE url = ?", (url,))
            return cur.fetchone() is not None

    def get_all(self, folder: str = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            if folder:
                cur = conn.execute("SELECT id, title, url, folder FROM bookmarks WHERE folder = ? ORDER BY id ASC", (folder,))
            else:
                cur = conn.execute("SELECT id, title, url, folder FROM bookmarks ORDER BY id ASC")
            return [dict(row) for row in cur.fetchall()]
