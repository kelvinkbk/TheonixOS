#!/usr/bin/env python3
"""
Theonix Messages — Unified AI Assistant & Communication Workspace for Theonix OS.
Powered by theonix_core platform services with drag-and-drop file sharing and Markdown syntax styling.
"""

import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")))

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QScrollArea, QFrame,
    QComboBox, QButtonGroup, QFileDialog, QMessageBox, QInputDialog
)

from theonix_core import (
    THEONIX_THEME_QSS, GlassCard, NavButton, Badge,
    apply_theonix_style, AIService
)

DB_PATH = os.path.expanduser("~/.config/theonix/messages.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT,
            sender TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def format_markdown(text: str) -> str:
    """Format basic markdown code blocks and inline formatting to styled HTML."""
    formatted = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _code_block_repl(m):
        code = m.group(1)
        return f"<pre style='background:#07090E;padding:12px;border-radius:8px;border:1px solid rgba(0,255,170,0.25);font-family:monospace;color:#00FFAA;margin:8px 0;'>{code}</pre>"
    formatted = re.sub(r"```(?:[a-zA-Z0-9_-]+)?\n(.*?)```", _code_block_repl, formatted, flags=re.DOTALL)

    formatted = re.sub(r"`([^`]+)`", r"<code style='background:rgba(255,255,255,0.08);padding:2px 6px;border-radius:4px;color:#00FFAA;font-family:monospace;'>\1</code>", formatted)
    formatted = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", formatted)
    formatted = formatted.replace("\n", "<br/>")
    return formatted


class StreamWorker(QThread):
    chunk = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, prompt: str, model: str):
        super().__init__()
        self.prompt = prompt
        self.model = model

    def run(self):
        try:
            p = subprocess.Popen(
                ["ollama", "run", self.model, self.prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            for line in p.stdout:
                self.chunk.emit(line)
            p.wait()
        except Exception as e:
            self.chunk.emit(f"\n[Error: {e}]\n")
        self.done.emit()


class MessageDropArea(QTextEdit):
    """Text edit input with drag-and-drop file attachment support from Theonix Files."""
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    self.file_dropped.emit(file_path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class TheonixMessagesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Messages")
        self.setMinimumSize(980, 700)
        self.resize(1100, 760)
        self.current_thread = "thaid_system"
        self.worker = None

        init_db()

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar Container
        sidebar_box = QWidget()
        sidebar_box.setObjectName("SidebarContainer")
        sidebar_box.setFixedWidth(260)
        sb_layout = QVBoxLayout(sidebar_box)
        sb_layout.setContentsMargins(0, 18, 0, 18)
        sb_layout.setSpacing(4)

        # Brand header
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(20, 0, 20, 14)
        brand_icon = QLabel("💬")
        brand_icon.setStyleSheet("font-size: 18px;")
        brand_title = QLabel("THEONIX")
        brand_title.setStyleSheet("font-size: 14px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;")
        brand_tag = Badge("MESSAGES", "cyan")
        
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title)
        brand_row.addWidget(brand_tag)
        brand_row.addStretch()
        sb_layout.addLayout(brand_row)

        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(14, 0, 14, 10)
        new_btn = QPushButton("➕  New Chat")
        new_btn.setProperty("class", "PrimaryBtn")
        new_btn.setFixedHeight(38)
        new_btn.clicked.connect(self._new_chat)
        btn_box.addWidget(new_btn)
        sb_layout.addLayout(btn_box)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.threads = [
            ("🤖  THAID Assistant", "thaid_system"),
            ("💻  Shell & Linux Helper", "shell_helper"),
            ("⚡  Code & Debugging", "code_helper"),
            ("📝  Notes & Drafting", "notes_draft"),
        ]

        self.thread_btn_map = {}
        for idx, (name, tid) in enumerate(self.threads):
            btn = NavButton(name)
            self.btn_group.addButton(btn, idx)
            self.thread_btn_map[idx] = tid
            sb_layout.addWidget(btn)

        sb_layout.addStretch()
        main_layout.addWidget(sidebar_box)

        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(28, 20, 28, 20)
        right_layout.setSpacing(14)

        # Top Bar
        top_bar = QHBoxLayout()
        self.chat_title = QLabel("🤖  THAID Assistant")
        self.chat_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        top_bar.addWidget(self.chat_title)
        top_bar.addStretch()

        self.model_selector = QComboBox()
        self.model_selector.addItems(["llama3.2:1b", "mistral", "deepseek-r1:1.5b", "phi3", "qwen2.5:1.5b"])
        top_bar.addWidget(QLabel("Model:"))
        top_bar.addWidget(self.model_selector)

        export_btn = QPushButton("Export .md")
        export_btn.setProperty("class", "ActionBtn")
        export_btn.clicked.connect(self._export_chat)
        top_bar.addWidget(export_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "ActionBtn")
        clear_btn.clicked.connect(self._clear_history)
        top_bar.addWidget(clear_btn)
        right_layout.addLayout(top_bar)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: rgba(14, 18, 28, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; color: #F8FAFC; font-size: 13.5px;")
        right_layout.addWidget(self.chat_display, 1)

        # Quick Action Prompt Chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        
        prompt_chips = [
            ("⚡ Snapshot Btrfs", "Show me how to snapshot Btrfs before updates."),
            ("🐧 Linux System Info", "Explain how to check memory, kernel, and hardware on Theonix OS."),
            ("🐍 Python Script", "Write a Python script to monitor system temperature and disk usage."),
            ("🛠️ Git Conflict Help", "How do I safely resolve a git merge conflict step by step?"),
        ]
        for c_label, c_prompt in prompt_chips:
            c_btn = QPushButton(c_label)
            c_btn.setProperty("class", "ActionBtn")
            c_btn.clicked.connect(lambda _, p=c_prompt: self._insert_prompt(p))
            chips_row.addWidget(c_btn)

        chips_row.addStretch()
        right_layout.addLayout(chips_row)

        bottom_box = QHBoxLayout()
        bottom_box.setSpacing(12)

        self.msg_input = MessageDropArea()
        self.msg_input.setFixedHeight(75)
        self.msg_input.setPlaceholderText("Type a message or drag a file from Theonix Files here...")
        self.msg_input.setStyleSheet("background-color: rgba(18, 24, 38, 0.95); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px 16px; color: #FFFFFF; font-size: 13.5px;")
        self.msg_input.file_dropped.connect(self._on_file_dropped)
        bottom_box.addWidget(self.msg_input, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setProperty("class", "PrimaryBtn")
        self.send_btn.setFixedHeight(75)
        self.send_btn.clicked.connect(self._send_message)
        bottom_box.addWidget(self.send_btn)

        right_layout.addLayout(bottom_box)
        main_layout.addWidget(right_panel, 1)

        self.btn_group.idClicked.connect(self._on_thread_changed)
        first_btn = self.btn_group.button(0)
        if first_btn:
            first_btn.setChecked(True)
        self._load_history()

    def _on_file_dropped(self, file_path: str):
        self.msg_input.append(f"[Attached file: {file_path}]\nPlease inspect and analyze this file.")

    def _insert_prompt(self, prompt_text: str):
        self.msg_input.setText(prompt_text)
        self._send_message()

    def _on_thread_changed(self, idx):
        tid = self.thread_btn_map.get(idx, "thaid_system")
        self.current_thread = tid
        btn = self.btn_group.button(idx)
        if btn:
            self.chat_title.setText(btn.text())
        self._load_history()

    def _new_chat(self):
        tid = f"chat_{datetime.now().strftime('%m%d_%H%M%S')}"
        idx = len(self.thread_btn_map)
        btn = NavButton(f"💬  Chat {datetime.now().strftime('%H:%M')}")
        self.btn_group.addButton(btn, idx)
        self.thread_btn_map[idx] = tid
        btn.setChecked(True)
        self._on_thread_changed(idx)

    def _load_history(self):
        self.chat_display.clear()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT sender, content, timestamp FROM messages WHERE thread_id = ? ORDER BY id ASC", (self.current_thread,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            self.chat_display.setHtml(
                "<div style='color:#64748B;padding:30px;text-align:center;font-family:sans-serif;'>"
                "<h3 style='color:#FFFFFF;margin-bottom:8px;'>Theonix Messages &amp; AI Workspace</h3>"
                "<p>Private local intelligence running directly on your device with Ollama &amp; THAID.</p>"
                "</div>"
            )
        else:
            html = ""
            for sender, content, ts in rows:
                if sender == "user":
                    html += f"<div style='margin-bottom:14px;'><b style='color:#00FFAA;'>You:</b><br/><span style='color:#F8FAFC;'>{format_markdown(content)}</span></div>"
                else:
                    html += f"<div style='margin-bottom:16px;background:rgba(20,26,40,0.85);padding:14px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);'><b style='color:#6C63FF;'>THAID:</b><br/><span style='color:#E2E8F0;'>{format_markdown(content)}</span></div>"
            self.chat_display.setHtml(html)

    def _send_message(self):
        text = self.msg_input.toPlainText().strip()
        if not text:
            return
        self.msg_input.clear()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (thread_id, sender, content) VALUES (?, ?, ?)", (self.current_thread, "user", text))
        conn.commit()
        conn.close()

        self._load_history()
        self.chat_display.append("<br/><b style='color:#6C63FF;'>THAID:</b> <i>Thinking...</i><br/>")

        model = self.model_selector.currentText()
        self.worker = StreamWorker(text, model)
        self.current_ai_response = []

        def _on_chunk(c):
            self.current_ai_response.append(c)
            self.chat_display.insertPlainText(c)

        def _on_done():
            full_ans = "".join(self.current_ai_response)
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO messages (thread_id, sender, content) VALUES (?, ?, ?)", (self.current_thread, "assistant", full_ans))
            conn.commit()
            conn.close()
            self._load_history()

        self.worker.chunk.connect(_on_chunk)
        self.worker.done.connect(_on_done)
        self.worker.start()

    def _export_chat(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT sender, content, timestamp FROM messages WHERE thread_id = ? ORDER BY id ASC", (self.current_thread,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            QMessageBox.information(self, "Export", "Chat thread is empty.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Chat", os.path.expanduser(f"~/chat_{self.current_thread}.md"), "Markdown Files (*.md)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Theonix Messages Export — {self.current_thread}\n\n")
                for s, c, ts in rows:
                    f.write(f"### {s.upper()} ({ts})\n\n{c}\n\n---\n\n")
            QMessageBox.information(self, "Export", f"Chat exported successfully to {file_path}")

    def _clear_history(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE thread_id = ?", (self.current_thread,))
        conn.commit()
        conn.close()
        self._load_history()


def main():
    app = QApplication(sys.argv)
    apply_theonix_style(app)
    win = TheonixMessagesWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
