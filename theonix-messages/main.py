#!/usr/bin/env python3
"""
Theonix Messages — AI Assistant & Communications Hub for Theonix OS
Connects directly to local THAID daemon & Ollama models for private, rapid AI chat.
"""

import os
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QFrame, QSplitter, QComboBox, QMessageBox, QScrollArea
)

DB_PATH = os.path.expanduser("~/.config/theonix/messages.db")

THEME_QSS = """
QMainWindow {
    background-color: #0B0E14;
}

QWidget#CentralWidget {
    background-color: #0B0E14;
    color: #F0F4F8;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Sidebar */
QListWidget#ThreadList {
    background-color: #121620;
    border: none;
    border-right: 1px solid #1E2638;
    outline: none;
    padding-top: 12px;
}

QListWidget#ThreadList::item {
    color: #94A3B8;
    height: 52px;
    padding-left: 14px;
    margin: 3px 8px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
}

QListWidget#ThreadList::item:hover {
    background-color: rgba(108, 99, 255, 0.12);
    color: #FFFFFF;
}

QListWidget#ThreadList::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    font-weight: bold;
}

/* Chat Log */
QTextEdit#ChatDisplay {
    background-color: #0F131C;
    border: 1px solid #1E2638;
    border-radius: 10px;
    padding: 16px;
    color: #F0F4F8;
    font-size: 14px;
}

/* Input Area */
QTextEdit#MessageInput {
    background-color: #161D2B;
    border: 1px solid #28354D;
    border-radius: 10px;
    padding: 10px 14px;
    color: #FFFFFF;
    font-size: 14px;
}

QTextEdit#MessageInput:focus {
    border: 1px solid #00FFAA;
}

QPushButton#SendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFAA, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: bold;
    padding: 12px 24px;
}

QPushButton#SendBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #24FFBA, stop:1 #1CE0FF);
}

QPushButton.ActionBtn {
    background-color: #21293A;
    color: #F0F4F8;
    border: 1px solid #2F3B52;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

QPushButton.ActionBtn:hover {
    background-color: #2D374E;
    color: #00FFAA;
}
"""


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


class TheonixMessagesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Messages")
        self.setMinimumSize(960, 680)
        self.resize(1080, 740)
        self.current_thread = "thaid_system"
        self.worker = None

        init_db()

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar: Threads / AI Personas
        left_panel = QWidget()
        left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 16, 12, 16)
        left_layout.setSpacing(12)

        new_btn = QPushButton("➕  New Chat")
        new_btn.setObjectName("SendBtn")
        new_btn.clicked.connect(self._new_chat)
        left_layout.addWidget(new_btn)

        self.thread_list = QListWidget()
        self.thread_list.setObjectName("ThreadList")
        
        threads = [
            ("🤖  THAID System AI", "thaid_system"),
            ("💻  Shell & Linux Helper", "shell_helper"),
            ("⚡  Code & Debugging", "code_helper"),
            ("📝  Notes & Drafting", "notes_draft"),
        ]
        for name, tid in threads:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self.thread_list.addItem(item)

        self.thread_list.currentRowChanged.connect(self._on_thread_changed)
        left_layout.addWidget(self.thread_list)

        main_layout.addWidget(left_panel)

        # Right Panel: Chat viewport and input
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(24, 18, 24, 18)
        right_layout.setSpacing(14)

        # Top Bar
        top_bar = QHBoxLayout()
        self.chat_title = QLabel("🤖  THAID System AI")
        self.chat_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        top_bar.addWidget(self.chat_title)
        top_bar.addStretch()

        self.model_selector = QComboBox()
        self.model_selector.addItems(["llama3.2:1b", "mistral", "deepseek-r1:1.5b", "phi3", "qwen2.5:1.5b"])
        top_bar.addWidget(QLabel("Model:"))
        top_bar.addWidget(self.model_selector)

        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("class", "ActionBtn")
        clear_btn.clicked.connect(self._clear_history)
        top_bar.addWidget(clear_btn)
        right_layout.addLayout(top_bar)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("ChatDisplay")
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display, 1)

        # Bottom Input
        bottom_box = QHBoxLayout()
        bottom_box.setSpacing(10)

        self.msg_input = QTextEdit()
        self.msg_input.setObjectName("MessageInput")
        self.msg_input.setFixedHeight(70)
        self.msg_input.setPlaceholderText("Type a message or command (e.g. 'How do I configure btrfs snapshots?')...")
        bottom_box.addWidget(self.msg_input, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("SendBtn")
        self.send_btn.setFixedHeight(70)
        self.send_btn.clicked.connect(self._send_message)
        bottom_box.addWidget(self.send_btn)

        right_layout.addLayout(bottom_box)
        main_layout.addWidget(right_panel, 1)

        self.thread_list.setCurrentRow(0)
        self._load_history()

    def _on_thread_changed(self, idx):
        item = self.thread_list.item(idx)
        if item:
            self.current_thread = item.data(Qt.ItemDataRole.UserRole)
            self.chat_title.setText(item.text())
            self._load_history()

    def _new_chat(self):
        tid = f"chat_{datetime.now().strftime('%m%d_%H%M%S')}"
        item = QListWidgetItem(f"💬  Chat {datetime.now().strftime('%H:%M')}")
        item.setData(Qt.ItemDataRole.UserRole, tid)
        self.thread_list.addItem(item)
        self.thread_list.setCurrentItem(item)

    def _load_history(self):
        self.chat_display.clear()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT sender, content, timestamp FROM messages WHERE thread_id = ? ORDER BY id ASC", (self.current_thread,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            self.chat_display.setHtml(
                "<div style='color:#64748B;padding:20px;text-align:center;'>"
                "<h3>Welcome to Theonix Messages</h3>"
                "<p>Ask questions, generate system scripts, or chat with local AI privately.</p>"
                "</div>"
            )
        else:
            html = ""
            for sender, content, ts in rows:
                if sender == "user":
                    html += f"<div style='margin-bottom:12px;'><b style='color:#00FFAA;'>You:</b><br/><span style='color:#F0F4F8;'>{content}</span></div>"
                else:
                    html += f"<div style='margin-bottom:16px;background:#161D2B;padding:12px;border-radius:8px;'><b style='color:#6C63FF;'>THAID:</b><br/><span style='color:#E2E8F0;'>{content}</span></div>"
            self.chat_display.setHtml(html)

    def _send_message(self):
        text = self.msg_input.toPlainText().strip()
        if not text:
            return
        self.msg_input.clear()

        # Save user msg
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

        self.worker.chunk.connect(_on_chunk)
        self.worker.done.connect(_on_done)
        self.worker.start()

    def _clear_history(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE thread_id = ?", (self.current_thread,))
        conn.commit()
        conn.close()
        self._load_history()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME_QSS)
    win = TheonixMessagesWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
