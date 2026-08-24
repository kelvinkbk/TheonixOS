#!/usr/bin/env python3
"""
Theonix Browser — Fast, Ultra-Dark Glassmorphic Web Browser for Theonix OS.
Powered by theonix_core platform services with integrated THAID AI assistant.
"""

import os
import subprocess
import sys
import threading
import urllib.parse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")))

from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QLabel, QSplitter, QTextEdit,
    QProgressBar, QToolBar, QFrame, QGridLayout, QTabBar
)

from theonix_core import (
    THEONIX_THEME_QSS, GlassCard, Badge, SearchBar,
    apply_theonix_style, AIService
)

HAS_WEBENGINE = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
    HAS_WEBENGINE = True
except ImportError:
    from PyQt6.QtWidgets import QTextBrowser

HOME_URL = "https://duckduckgo.com"

BROWSER_THEME_QSS = THEONIX_THEME_QSS + """
/* Browser Tabs at Top */
QTabWidget#BrowserTabs::pane {
    border: none;
    background-color: #07090E;
    margin: 0px;
    padding: 0px;
}

QTabBar {
    background-color: #0A0D15;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QTabBar::tab {
    background-color: #0E121C;
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    margin-right: 2px;
    margin-top: 4px;
    font-size: 12.5px;
    font-weight: 500;
    min-width: 140px;
    max-width: 220px;
}

QTabBar::tab:selected {
    background-color: #121826;
    color: #FFFFFF;
    border-color: rgba(0, 255, 170, 0.4);
    border-top: 2px solid #00FFAA;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.05);
    color: #E2E8F0;
}

/* Nav Toolbar */
QFrame#NavToolbar {
    background-color: #0E121C;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    padding: 8px 12px;
}

/* Bookmarks Bar */
QFrame#BookmarksBar {
    background-color: #0B0E17;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    padding: 4px 12px;
}

/* AI Sidebar */
QFrame#AISidebar {
    background-color: #0B0E17;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px;
}
"""


def render_fallback_page(url_or_query: str) -> str:
    """Renders a beautiful, rich dark-mode startpage or web search preview."""
    is_search = "duckduckgo.com/?q=" in url_or_query or "google.com" in url_or_query
    query = ""
    if "q=" in url_or_query:
        query = urllib.parse.unquote(url_or_query.split("q=", 1)[1].split("&")[0])

    if is_search and query:
        return f"""
        <div style="background-color:#07090E;color:#F8FAFC;font-family:'Segoe UI',sans-serif;padding:32px;min-height:100%;">
            <div style="max-width:780px;margin:0 auto;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:14px;">
                    <span style="font-size:24px;">🔍</span>
                    <div>
                        <h2 style="margin:0;font-size:18px;color:#FFFFFF;">Search Results for &ldquo;<span style="color:#00FFAA;">{query}</span>&rdquo;</h2>
                        <span style="color:#94A3B8;font-size:12px;">Query routed via privacy-first search index</span>
                    </div>
                </div>

                <div style="background:rgba(18,24,38,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;margin-bottom:16px;">
                    <div style="color:#00D4FF;font-size:12px;font-weight:bold;margin-bottom:4px;">https://theonixos.xyz &rsaquo; docs &rsaquo; {query}</div>
                    <a href="https://theonixos.xyz" style="color:#00FFAA;font-size:17px;font-weight:bold;text-decoration:none;">Theonix OS &mdash; Next-Generation AI-Augmented Linux Distribution</a>
                    <p style="color:#94A3B8;font-size:13px;line-height:1.5;margin-top:6px;">
                        Theonix OS combines Arch Linux speed, KDE Plasma 6 Wayland aesthetics, local THAID AI intelligence, and Universal App Compatibility Layer (UACL).
                    </p>
                </div>

                <div style="background:rgba(18,24,38,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;margin-bottom:16px;">
                    <div style="color:#00D4FF;font-size:12px;font-weight:bold;margin-bottom:4px;">https://wiki.archlinux.org &rsaquo; title &rsaquo; {query}</div>
                    <a href="https://wiki.archlinux.org" style="color:#6C63FF;font-size:17px;font-weight:bold;text-decoration:none;">ArchWiki Documentation &middot; Community Reference</a>
                    <p style="color:#94A3B8;font-size:13px;line-height:1.5;margin-top:6px;">
                        Comprehensive technical documentation, package guidelines, systemd services, PipeWire audio configuration, and Vulkan driver guides.
                    </p>
                </div>

                <div style="background:rgba(18,24,38,0.8);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px;">
                    <div style="color:#00D4FF;font-size:12px;font-weight:bold;margin-bottom:4px;">https://github.com/kelvinkbk/TheonixOS</div>
                    <a href="https://github.com/kelvinkbk/TheonixOS" style="color:#00FFAA;font-size:17px;font-weight:bold;text-decoration:none;">TheonixOS Official Repository on GitHub</a>
                    <p style="color:#94A3B8;font-size:13px;line-height:1.5;margin-top:6px;">
                        Open-source distribution source, Calamares branding, ISO build pipelines, and native Python applications suite.
                    </p>
                </div>
            </div>
        </div>
        """
    else:
        return f"""
        <div style="background-color:#07090E;color:#F8FAFC;font-family:'Segoe UI',sans-serif;padding:60px 30px;text-align:center;">
            <div style="max-width:650px;margin:0 auto;">
                <div style="width:64px;height:64px;margin:0 auto 20px;border-radius:18px;background:linear-gradient(135deg,#6C63FF,#00FFAA);display:flex;align-items:center;justify-content:center;font-size:32px;color:#0B0E14;font-weight:bold;">⚡</div>
                <h1 style="font-size:28px;font-weight:800;margin-bottom:10px;color:#FFFFFF;">Theonix Browser</h1>
                <p style="color:#94A3B8;font-size:14px;margin-bottom:30px;">Fast, private, and AI-augmented web navigation powered by local intelligence.</p>

                <div style="background:rgba(18,24,38,0.85);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:24px;text-align:left;">
                    <div style="font-weight:bold;color:#00FFAA;margin-bottom:8px;">Active URL / Resource:</div>
                    <a href="{url_or_query}" style="color:#00D4FF;font-size:14px;word-break:break-all;">{url_or_query}</a>
                    <p style="color:#94A3B8;font-size:12.5px;margin-top:12px;line-height:1.5;">
                        Tip: Install <code style="color:#00FFAA;">python-pyqt6-webengine</code> for full Chromium Blink rendering engine, or use the integrated THAID sidebar on the right to analyze and extract information.
                    </p>
                </div>
            </div>
        </div>
        """


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

        # 1. Navigation Toolbar
        nav_toolbar = QFrame()
        nav_toolbar.setObjectName("NavToolbar")
        t_layout = QHBoxLayout(nav_toolbar)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(8)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "ActionBtn")
        self.back_btn.clicked.connect(self._nav_back)
        t_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("▶")
        self.forward_btn.setProperty("class", "ActionBtn")
        self.forward_btn.clicked.connect(self._nav_forward)
        t_layout.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("🔄")
        self.reload_btn.setProperty("class", "ActionBtn")
        self.reload_btn.clicked.connect(self._nav_reload)
        t_layout.addWidget(self.reload_btn)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setProperty("class", "ActionBtn")
        self.home_btn.clicked.connect(lambda: self._navigate_to(HOME_URL))
        t_layout.addWidget(self.home_btn)

        # URL Bar with SSL indicator
        self.url_bar = SearchBar("Search or enter web address (Ctrl+L)...")
        self.url_bar.returnPressed.connect(self._on_url_entered)
        t_layout.addWidget(self.url_bar, 1)

        self.ai_toggle_btn = QPushButton("✨ Ask Theonix")
        self.ai_toggle_btn.setProperty("class", "PrimaryBtn")
        self.ai_toggle_btn.clicked.connect(self._toggle_ai_sidebar)
        t_layout.addWidget(self.ai_toggle_btn)

        self.new_tab_btn = QPushButton("➕")
        self.new_tab_btn.setProperty("class", "ActionBtn")
        self.new_tab_btn.clicked.connect(lambda: self.add_tab(HOME_URL, "New Tab"))
        t_layout.addWidget(self.new_tab_btn)

        main_layout.addWidget(nav_toolbar)

        # 2. Bookmarks Bar
        bmk_bar = QFrame()
        bmk_bar.setObjectName("BookmarksBar")
        bmk_layout = QHBoxLayout(bmk_bar)
        bmk_layout.setContentsMargins(0, 0, 0, 0)
        bmk_layout.setSpacing(6)

        bookmarks = [
            ("⚡ Theonix OS", "https://theonixos.xyz"),
            ("📖 Arch Wiki", "https://wiki.archlinux.org"),
            ("🟣 Flathub", "https://flathub.org"),
            ("🐙 GitHub", "https://github.com/kelvinkbk/TheonixOS"),
            ("🔍 DuckDuckGo", "https://duckduckgo.com"),
        ]
        for b_name, b_url in bookmarks:
            b_btn = QPushButton(b_name)
            b_btn.setProperty("class", "ActionBtn")
            b_btn.setStyleSheet("font-size: 12px; padding: 4px 10px;")
            b_btn.clicked.connect(lambda _, u=b_url: self._navigate_to(u))
            bmk_layout.addWidget(b_btn)
        bmk_layout.addStretch()
        main_layout.addWidget(bmk_bar)

        # 3. Main Splitter: Tabs Viewport + AI Assistant Drawer
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("BrowserTabs")
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.splitter.addWidget(self.tabs)

        # 4. AI Assistant Sidebar
        self.ai_sidebar = QFrame()
        self.ai_sidebar.setObjectName("AISidebar")
        self.ai_sidebar.setFixedWidth(330)
        ai_layout = QVBoxLayout(self.ai_sidebar)
        ai_layout.setContentsMargins(14, 16, 14, 16)
        ai_layout.setSpacing(10)

        ai_hdr = QHBoxLayout()
        ai_title = QLabel("🤖 Ask Theonix")
        ai_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00FFAA;")
        ai_hdr.addWidget(ai_title)
        ai_hdr.addStretch()
        ai_hdr.addWidget(Badge("ONLINE", "cyan"))
        ai_layout.addLayout(ai_hdr)

        pills_grid = QGridLayout()
        pills_grid.setSpacing(6)
        
        p1 = QPushButton("📝 Summarize")
        p1.setProperty("class", "ActionBtn")
        p1.clicked.connect(lambda: self._quick_prompt("Summarize the key information of this topic concisely."))

        p2 = QPushButton("💻 Extract Code")
        p2.setProperty("class", "ActionBtn")
        p2.clicked.connect(lambda: self._quick_prompt("Extract all code snippets, shell commands, and syntax blocks."))

        p3 = QPushButton("🔍 Explain Simply")
        p3.setProperty("class", "ActionBtn")
        p3.clicked.connect(lambda: self._quick_prompt("Explain the main concepts in simple terms with bullet points."))

        p4 = QPushButton("🌐 Translate")
        p4.setProperty("class", "ActionBtn")
        p4.clicked.connect(lambda: self._quick_prompt("Translate the content to clear English."))

        pills_grid.addWidget(p1, 0, 0)
        pills_grid.addWidget(p2, 0, 1)
        pills_grid.addWidget(p3, 1, 0)
        pills_grid.addWidget(p4, 1, 1)
        ai_layout.addLayout(pills_grid)

        self.ai_chat_log = QTextEdit()
        self.ai_chat_log.setReadOnly(True)
        self.ai_chat_log.setStyleSheet("background-color: rgba(14, 18, 28, 0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; color: #F8FAFC; padding: 10px; font-size: 13px;")
        self.ai_chat_log.setPlaceholderText("Ask THAID about this page or any topic...")
        ai_layout.addWidget(self.ai_chat_log)

        ai_input_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask AI...")
        self.ai_input.returnPressed.connect(self._send_ai_prompt)

        ai_send = QPushButton("Ask")
        ai_send.setProperty("class", "PrimaryBtn")
        ai_send.clicked.connect(self._send_ai_prompt)

        ai_input_row.addWidget(self.ai_input)
        ai_input_row.addWidget(ai_send)
        ai_layout.addLayout(ai_input_row)

        self.splitter.addWidget(self.ai_sidebar)
        self.ai_sidebar.setVisible(False)

        main_layout.addWidget(self.splitter, 1)

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab(HOME_URL, "New Tab"))
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self._close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+R"), self, self._nav_reload)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))

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
            view.setStyleSheet("background-color: #07090E; border: none; color: #F8FAFC;")
            view.setHtml(render_fallback_page(url))

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
                target = f"https://duckduckgo.com/?q={urllib.parse.quote(target)}"
        self._navigate_to(target)

    def _navigate_to(self, url: str):
        view = self.tabs.currentWidget()
        if HAS_WEBENGINE and view:
            view.setUrl(QUrl(url))
        elif view:
            view.setHtml(render_fallback_page(url))
        self.url_bar.setText(url)

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
        elif view:
            self._navigate_to(self.url_bar.text())

    def _toggle_ai_sidebar(self):
        self.ai_sidebar.setVisible(not self.ai_sidebar.isVisible())

    def _quick_prompt(self, p_text):
        self.ai_input.setText(p_text)
        self._send_ai_prompt()

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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(BROWSER_THEME_QSS)
    win = TheonixBrowserWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
