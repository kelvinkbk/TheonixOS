#!/usr/bin/env python3
"""
Theonix Browser — Fast, AI-Augmented Web Browser for Theonix OS
Features multi-tab navigation, privacy shields, and integrated THAID AI Assistant.
"""

import os
import sys
import subprocess
import threading
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QLabel, QSplitter, QTextEdit,
    QProgressBar, QToolBar, QMenu, QStatusBar, QMessageBox, QFrame
)

# Attempt to load QWebEngineView if available, else use a lightweight fallback browser viewer
HAS_WEBENGINE = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    HAS_WEBENGINE = True
except ImportError:
    from PyQt6.QtWidgets import QTextBrowser

THEME_QSS = """
QMainWindow {
    background-color: #0B0E14;
}

QWidget#CentralWidget {
    background-color: #0B0E14;
    color: #F0F4F8;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* ToolBar & Controls */
QToolBar {
    background-color: #121620;
    border-bottom: 1px solid #1E2638;
    padding: 6px;
    spacing: 8px;
}

QPushButton.NavBtn {
    background-color: #1A2232;
    color: #F0F4F8;
    border: 1px solid #28354D;
    border-radius: 6px;
    font-size: 14px;
    padding: 6px 12px;
}

QPushButton.NavBtn:hover {
    background-color: #26334D;
    color: #00FFAA;
}

QLineEdit#UrlBar {
    background-color: #161D2B;
    border: 1px solid #28354D;
    border-radius: 8px;
    padding: 8px 16px;
    color: #FFFFFF;
    font-size: 13px;
    selection-background-color: #6C63FF;
}

QLineEdit#UrlBar:focus {
    border: 1px solid #00FFAA;
    background-color: #1A2234;
}

/* Tab Bar */
QTabWidget::pane {
    border: none;
    background-color: #0B0E14;
}

QTabBar::tab {
    background-color: #121620;
    color: #94A3B8;
    border: 1px solid #1E2638;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    margin-right: 2px;
    font-size: 13px;
    min-width: 140px;
    max-width: 220px;
}

QTabBar::tab:selected {
    background-color: #19202E;
    color: #FFFFFF;
    border-color: #334155;
    border-top: 2px solid #00FFAA;
}

QTabBar::tab:hover:!selected {
    background-color: #161C2A;
    color: #E2E8F0;
}

/* AI Sidebar */
QFrame#AISidebar {
    background-color: #121620;
    border-left: 1px solid #1E2638;
    padding: 16px;
}

QTextEdit#AIChatLog {
    background-color: #161D2B;
    border: 1px solid #28354D;
    border-radius: 8px;
    color: #F0F4F8;
    padding: 8px;
    font-size: 13px;
}

QLineEdit#AIInput {
    background-color: #161D2B;
    border: 1px solid #28354D;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
}

QLineEdit#AIInput:focus {
    border: 1px solid #6C63FF;
}

QPushButton#AISendBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    padding: 8px 14px;
}
"""

HOME_URL = "https://duckduckgo.com"


class AIThread(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            cmd = ["ollama", "run", "llama3.2:1b", self.prompt]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in p.stdout:
                self.chunk_received.emit(line)
            p.wait()
        except Exception as e:
            self.chunk_received.emit(f"\n[AI Error: {e}]\n")
        self.finished.emit()


class TheonixBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Browser")
        self.setMinimumSize(1040, 720)
        self.resize(1200, 800)

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        main_layout.addWidget(self.toolbar)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "NavBtn")
        self.back_btn.clicked.connect(self._nav_back)
        self.toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("▶")
        self.forward_btn.setProperty("class", "NavBtn")
        self.forward_btn.clicked.connect(self._nav_forward)
        self.toolbar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("🔄")
        self.reload_btn.setProperty("class", "NavBtn")
        self.reload_btn.clicked.connect(self._nav_reload)
        self.toolbar.addWidget(self.reload_btn)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setProperty("class", "NavBtn")
        self.home_btn.clicked.connect(lambda: self._navigate_to(HOME_URL))
        self.toolbar.addWidget(self.home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("UrlBar")
        self.url_bar.setPlaceholderText("Search or enter web address...")
        self.url_bar.returnPressed.connect(self._on_url_entered)
        self.toolbar.addWidget(self.url_bar)

        self.ai_toggle_btn = QPushButton("✨ THAID AI")
        self.ai_toggle_btn.setProperty("class", "NavBtn")
        self.ai_toggle_btn.setStyleSheet("font-weight: bold; color: #00FFAA;")
        self.ai_toggle_btn.clicked.connect(self._toggle_ai_sidebar)
        self.toolbar.addWidget(self.ai_toggle_btn)

        self.new_tab_btn = QPushButton("➕")
        self.new_tab_btn.setProperty("class", "NavBtn")
        self.new_tab_btn.clicked.connect(lambda: self.add_tab(HOME_URL, "New Tab"))
        self.toolbar.addWidget(self.new_tab_btn)

        # Splitter: Tabs on Left, AI Assistant Sidebar on Right
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.splitter.addWidget(self.tabs)

        # AI Sidebar
        self.ai_sidebar = QFrame()
        self.ai_sidebar.setObjectName("AISidebar")
        self.ai_sidebar.setFixedWidth(320)
        ai_layout = QVBoxLayout(self.ai_sidebar)
        ai_layout.setContentsMargins(12, 12, 12, 12)
        ai_layout.setSpacing(10)

        ai_header = QLabel("🤖  THAID Assistant")
        ai_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FFAA;")
        ai_layout.addWidget(ai_header)

        # Quick AI Actions
        q_row = QHBoxLayout()
        sum_btn = QPushButton("Summarize")
        sum_btn.clicked.connect(self._ai_summarize)
        code_btn = QPushButton("Extract Code")
        code_btn.clicked.connect(self._ai_extract_code)
        q_row.addWidget(sum_btn)
        q_row.addWidget(code_btn)
        ai_layout.addLayout(q_row)

        self.ai_chat_log = QTextEdit()
        self.ai_chat_log.setObjectName("AIChatLog")
        self.ai_chat_log.setReadOnly(True)
        self.ai_chat_log.setPlaceholderText("Ask THAID about this webpage or anything...")
        ai_layout.addWidget(self.ai_chat_log)

        ai_input_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setObjectName("AIInput")
        self.ai_input.setPlaceholderText("Ask AI...")
        self.ai_input.returnPressed.connect(self._send_ai_prompt)

        ai_send = QPushButton("Ask")
        ai_send.setObjectName("AISendBtn")
        ai_send.clicked.connect(self._send_ai_prompt)

        ai_input_row.addWidget(self.ai_input)
        ai_input_row.addWidget(ai_send)
        ai_layout.addLayout(ai_input_row)

        self.splitter.addWidget(self.ai_sidebar)
        self.ai_sidebar.setVisible(False)

        main_layout.addWidget(self.splitter)

        # Initial Tab
        self.add_tab(HOME_URL, "DuckDuckGo")

    def add_tab(self, url: str, title: str):
        if HAS_WEBENGINE:
            view = QWebEngineView()
            view.setUrl(QUrl(url))
            view.titleChanged.connect(lambda t: self._update_tab_title(view, t))
            view.urlChanged.connect(lambda u: self._update_url_bar(view, u))
        else:
            view = QTextBrowser()
            view.setOpenExternalLinks(True)
            view.setHtml(f"<div style='color:white;padding:30px;font-family:sans-serif;'><h2>Theonix Browser</h2><p>Viewing: <a style='color:#00FFAA;' href='{url}'>{url}</a></p><p>Powered by Qt.</p></div>")

        idx = self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(idx)

    def _update_tab_title(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx != -1:
            self.tabs.setTabText(idx, title[:18] + ("..." if len(title) > 18 else ""))

    def _update_url_bar(self, view, url):
        if self.tabs.currentWidget() == view:
            self.url_bar.setText(url.toString())

    def _close_tab(self, idx):
        if self.tabs.count() > 1:
            widget = self.tabs.widget(idx)
            self.tabs.removeTab(idx)
            widget.deleteLater()

    def _on_tab_changed(self, idx):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            self.url_bar.setText(view.url().toString())

    def _on_url_entered(self):
        target = self.url_bar.text().strip()
        if not target:
            return
        if not (target.startswith("http://") or target.startswith("https://")):
            if "." in target and " " not in target:
                target = "https://" + target
            else:
                target = f"https://duckduckgo.com/?q={target.replace(' ', '+')}"
        self._navigate_to(target)

    def _navigate_to(self, url: str):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            view.setUrl(QUrl(url))
        elif view:
            view.setHtml(f"<div style='color:white;padding:30px;font-family:sans-serif;'><h2>Loading: {url}</h2></div>")

    def _nav_back(self):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            view.back()

    def _nav_forward(self):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            view.forward()

    def _nav_reload(self):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            view.reload()

    def _toggle_ai_sidebar(self):
        self.ai_sidebar.setVisible(not self.ai_sidebar.isVisible())

    def _send_ai_prompt(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_chat_log.append(f"<b>You:</b> {text}\n")
        self.ai_input.clear()
        self.ai_chat_log.append("<b>THAID:</b> <i>Thinking...</i>\n")

        self.ai_worker = AIThread(text)
        self.ai_worker.chunk_received.connect(lambda chunk: self.ai_chat_log.append(chunk))
        self.ai_worker.start()

    def _ai_summarize(self):
        self.ai_input.setText("Please summarize the main points of this topic.")
        self._send_ai_prompt()

    def _ai_extract_code(self):
        self.ai_input.setText("Extract and format all code snippets and commands.")
        self._send_ai_prompt()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME_QSS)
    win = TheonixBrowserWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
