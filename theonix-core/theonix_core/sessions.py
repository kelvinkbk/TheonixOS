"""
Theonix Core — Session Manager.
Persistent multi-session conversation memory across Desktop Orb, Browser, Messages, and CLI.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
import time

DB_PATH = os.path.expanduser("~/.config/theonix/thaid_sessions.db")


class SessionManager:
    """Manages separate conversation threads and contexts for different Theonix surfaces."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                surface TEXT NOT NULL,
                title TEXT,
                created_at REAL,
                updated_at REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    def create_or_get_session(self, session_id: str, surface: str = "general", title: str = "New Session") -> str:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        now = time.time()
        if not row:
            cur.execute(
                "INSERT INTO sessions (id, surface, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, surface, title, now, now)
            )
            conn.commit()
        conn.close()
        return session_id

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[str] = None):
        self.create_or_get_session(session_id)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        now = time.time()
        cur.execute(
            "INSERT INTO messages (session_id, role, content, metadata, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, metadata, now)
        )
        cur.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
        conn.commit()
        conn.close()

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        )
        rows = cur.fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear_session(self, session_id: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()


session_mgr = SessionManager()
