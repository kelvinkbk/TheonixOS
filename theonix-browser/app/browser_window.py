"""
Theonix Browser — Main Browser Window.
Integrates QtWebEngine, dynamic tab stack, smart address bar, THAID AI, history, bookmarks, and downloads.
"""

import os
import urllib.parse
from typing import List

from PyQt6.QtCore import Qt, QUrl, QKeySequence
from PyQt6.QtGui import QIcon, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSplitter, QStackedWidget, QTabBar, QFrame, QMessageBox,
    QProgressBar
)

from theonix_core import (
    THEONIX_THEME_QSS, GlassCard, Badge, SearchBar
)

from .web_view import TheonixWebView, HAS_WEBENGINE
from .history_manager import HistoryManager
from .bookmarks_manager import BookmarksManager
from .downloads_manager import DownloadsManager
from .ai_assistant import AskTheonixDrawer
from .new_tab_page import get_new_tab_html
from .settings_dialog import BrowserSettingsDialog
from .history_dialog import HistoryViewerDialog
from .downloads_dialog import DownloadsDialog

BROWSER_THEME_QSS = THEONIX_THEME_QSS + """
/* Top Window Tabs Header */
QTabBar#TopTabBar {
    background-color: #0A0D15;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

QTabBar#TopTabBar::tab {
    background-color: #0E121C;
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    margin-right: 2px;
    margin-top: 5px;
    font-size: 12.5px;
    font-weight: 500;
    min-width: 140px;
    max-width: 220px;
}

QTabBar#TopTabBar::tab:selected {
    background-color: #121826;
    color: #FFFFFF;
    border-color: rgba(0, 255, 170, 0.4);
    border-top: 2px solid #00FFAA;
    font-weight: 600;
}

QTabBar#TopTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.05);
    color: #E2E8F0;
}

/* Nav Toolbar */
QFrame#NavToolbar {
    background-color: #0E121C;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    padding: 8px 14px;
}

/* Bookmarks Bar */
QFrame#BookmarksBar {
    background-color: #0B0E17;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 4px 14px;
}

/* AI Sidebar */
QFrame#AISidebar {
    background-color: #0B0E17;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px;
}
"""


class TheonixBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Browser")
        self.setMinimumSize(1040, 720)
        self.resize(1240, 820)

        # Managers
        self.history_mgr = HistoryManager()
        self.bookmarks_mgr = BookmarksManager()
        self.downloads_mgr = DownloadsManager()

        self.search_engine = "DuckDuckGo"
        self.homepage = "https://duckduckgo.com"
        self.closed_tabs_stack: List[str] = []

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. TOP TAB BAR (Row 1)
        tab_header = QFrame()
        tab_header.setStyleSheet("background-color: #0A0D15; border-bottom: 1px solid rgba(255,255,255,0.08);")
        th_layout = QHBoxLayout(tab_header)
        th_layout.setContentsMargins(8, 4, 8, 0)
        th_layout.setSpacing(6)

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("TopTabBar")
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        th_layout.addWidget(self.tab_bar, 1)

        self.new_tab_btn = QPushButton("➕")
        self.new_tab_btn.setProperty("class", "ActionBtn")
        self.new_tab_btn.setFixedHeight(30)
        self.new_tab_btn.clicked.connect(lambda: self.add_tab("theonix://newtab", "New Tab"))
        th_layout.addWidget(self.new_tab_btn)

        main_layout.addWidget(tab_header)

        # 2. NAVIGATION TOOLBAR (Row 2)
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
        self.home_btn.clicked.connect(lambda: self._navigate_to(self.homepage))
        t_layout.addWidget(self.home_btn)

        # Smart Address Bar
        self.url_bar = SearchBar("Search or enter web address (Ctrl+L)...")
        self.url_bar.returnPressed.connect(self._on_url_entered)
        t_layout.addWidget(self.url_bar, 1)

        self.bookmark_btn = QPushButton("⭐")
        self.bookmark_btn.setProperty("class", "ActionBtn")
        self.bookmark_btn.setToolTip("Bookmark this page (Ctrl+D)")
        self.bookmark_btn.clicked.connect(self._toggle_bookmark_current)
        t_layout.addWidget(self.bookmark_btn)

        self.ai_toggle_btn = QPushButton("✨ Ask Theonix")
        self.ai_toggle_btn.setProperty("class", "PrimaryBtn")
        self.ai_toggle_btn.clicked.connect(self._toggle_ai_sidebar)
        t_layout.addWidget(self.ai_toggle_btn)

        self.downloads_btn = QPushButton("📥")
        self.downloads_btn.setProperty("class", "ActionBtn")
        self.downloads_btn.setToolTip("Downloads (Ctrl+J)")
        self.downloads_btn.clicked.connect(self._open_downloads_dialog)
        t_layout.addWidget(self.downloads_btn)

        self.history_btn = QPushButton("📜")
        self.history_btn.setProperty("class", "ActionBtn")
        self.history_btn.setToolTip("History (Ctrl+H)")
        self.history_btn.clicked.connect(self._open_history_dialog)
        t_layout.addWidget(self.history_btn)

        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setProperty("class", "ActionBtn")
        self.settings_btn.setToolTip("Browser Settings")
        self.settings_btn.clicked.connect(self._open_settings_dialog)
        t_layout.addWidget(self.settings_btn)

        main_layout.addWidget(nav_toolbar)

        # Loading Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { background: transparent; border: none; } QProgressBar::chunk { background: #00FFAA; }")
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 3. BOOKMARKS BAR (Row 3)
        self.bmk_bar = QFrame()
        self.bmk_bar.setObjectName("BookmarksBar")
        self.bmk_layout = QHBoxLayout(self.bmk_bar)
        self.bmk_layout.setContentsMargins(0, 0, 0, 0)
        self.bmk_layout.setSpacing(6)
        main_layout.addWidget(self.bmk_bar)
        self._refresh_bookmarks_bar()

        # 4. VIEWPORT SPLITTER & AI DRAWER (Row 4 - 100% Height)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.view_stack = QStackedWidget()
        self.view_stack.setStyleSheet("background-color: #07090E;")
        self.splitter.addWidget(self.view_stack)

        self.ai_sidebar = AskTheonixDrawer(self._get_current_view, self)
        self.splitter.addWidget(self.ai_sidebar)
        self.ai_sidebar.setVisible(False)

        main_layout.addWidget(self.splitter, 1)

        # Connect downloads handling
        if HAS_WEBENGINE:
            from PyQt6.QtWebEngineCore import QWebEngineProfile
            profile = QWebEngineProfile.defaultProfile()
            if hasattr(profile, "downloadRequested"):
                profile.downloadRequested.connect(self.downloads_mgr.handle_download_request)

        # Keyboard shortcuts
        self._setup_shortcuts()

        # Initial Tab
        self.add_tab("https://duckduckgo.com", "DuckDuckGo")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab("theonix://newtab", "New Tab"))
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self._close_tab(self.tab_bar.currentIndex()))
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self._restore_closed_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, self._nav_reload)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("Ctrl+D"), self, self._toggle_bookmark_current)
        QShortcut(QKeySequence("Ctrl+H"), self, self._open_history_dialog)
        QShortcut(QKeySequence("Ctrl+J"), self, self._open_downloads_dialog)
        QShortcut(QKeySequence("Ctrl++"), self, lambda: self._get_current_view().zoom_in() if self._get_current_view() else None)
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self._get_current_view().zoom_out() if self._get_current_view() else None)
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self._get_current_view().reset_zoom() if self._get_current_view() else None)

    def _get_current_view(self) -> TheonixWebView:
        return self.view_stack.currentWidget()

    def add_tab(self, url: str, title: str = "New Tab"):
        view = TheonixWebView(parent=self)
        
        # Connect signals
        view.title_updated.connect(lambda t: self._update_tab_title(view, t))
        view.url_updated.connect(lambda u: self._update_tab_url(view, u))
        view.load_progress_changed.connect(self._on_load_progress)
        view.new_window_requested.connect(lambda u: self.add_tab(u.toString() if u.isValid() else "theonix://newtab", "New Tab"))

        if url == "theonix://newtab":
            recent = self.history_mgr.get_recent(limit=8)
            bmks = self.bookmarks_mgr.get_all()
            if not HAS_WEBENGINE:
                view.browser.setHtml(get_new_tab_html(bmks, recent))
            else:
                view.setHtml(get_new_tab_html(bmks, recent))
        else:
            view.load_url(QUrl(url))

        view.setProperty("current_url", url)
        idx = self.view_stack.addWidget(view)
        t_idx = self.tab_bar.addTab(title)
        self.tab_bar.setCurrentIndex(t_idx)
        self.view_stack.setCurrentIndex(idx)

    def _update_tab_title(self, view, title):
        idx = self.view_stack.indexOf(view)
        if idx != -1:
            clean = title[:18] + ("..." if len(title) > 18 else "")
            self.tab_bar.setTabText(idx, clean)

    def _update_tab_url(self, view, url: QUrl):
        url_str = url.toString()
        view.setProperty("current_url", url_str)
        if self.view_stack.currentWidget() == view:
            self.url_bar.setText(url_str)
            self._update_bookmark_icon(url_str)

        # Record in persistent history
        if not url_str.startswith("theonix://") and not url_str.startswith("about:"):
            title = self.tab_bar.tabText(self.view_stack.indexOf(view))
            self.history_mgr.add_entry(url_str, title)

    def _on_load_progress(self, progress: int):
        if 0 < progress < 100:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setVisible(False)

    def _close_tab(self, idx):
        if self.tab_bar.count() > 1:
            view = self.view_stack.widget(idx)
            if view:
                url_str = view.property("current_url")
                if url_str:
                    self.closed_tabs_stack.append(url_str)
                self.tab_bar.removeTab(idx)
                self.view_stack.removeWidget(view)
                view.deleteLater()

    def _restore_closed_tab(self):
        if self.closed_tabs_stack:
            last_url = self.closed_tabs_stack.pop()
            self.add_tab(last_url, "Restored Tab")

    def _on_tab_changed(self, idx):
        if 0 <= idx < self.view_stack.count():
            self.view_stack.setCurrentIndex(idx)
            view = self.view_stack.widget(idx)
            if view:
                url_str = view.property("current_url") or self.homepage
                self.url_bar.setText(url_str)
                self._update_bookmark_icon(url_str)

    def _on_url_entered(self):
        target = self.url_bar.text().strip()
        if not target:
            return

        if not (target.startswith("http://") or target.startswith("https://") or target.startswith("theonix://")):
            if "." in target and " " not in target:
                target = "https://" + target
            else:
                tmpl = BrowserSettingsDialog.SEARCH_ENGINES.get(self.search_engine, "https://duckduckgo.com/?q={query}")
                target = tmpl.format(query=urllib.parse.quote(target))

        self._navigate_to(target)

    def _navigate_to(self, url: str):
        view = self._get_current_view()
        if not view:
            return
        if url == "theonix://newtab":
            recent = self.history_mgr.get_recent(limit=8)
            bmks = self.bookmarks_mgr.get_all()
            if not HAS_WEBENGINE:
                view.browser.setHtml(get_new_tab_html(bmks, recent))
            else:
                view.setHtml(get_new_tab_html(bmks, recent))
        else:
            view.load_url(QUrl(url))
        self.url_bar.setText(url)
        self._update_bookmark_icon(url)

    def _nav_back(self):
        view = self._get_current_view()
        if HAS_WEBENGINE and view and hasattr(view, "back"):
            view.back()

    def _nav_forward(self):
        view = self._get_current_view()
        if HAS_WEBENGINE and view and hasattr(view, "forward"):
            view.forward()

    def _nav_reload(self):
        view = self._get_current_view()
        if HAS_WEBENGINE and view and hasattr(view, "reload"):
            view.reload()
        elif view:
            self._navigate_to(self.url_bar.text())

    def _toggle_ai_sidebar(self):
        self.ai_sidebar.setVisible(not self.ai_sidebar.isVisible())

    def _toggle_bookmark_current(self):
        url = self.url_bar.text().strip()
        if not url or url.startswith("theonix://"):
            return
        if self.bookmarks_mgr.is_bookmarked(url):
            self.bookmarks_mgr.remove_bookmark(url)
        else:
            cur_title = self.tab_bar.tabText(self.tab_bar.currentIndex())
            self.bookmarks_mgr.add_bookmark(cur_title, url)
        self._update_bookmark_icon(url)
        self._refresh_bookmarks_bar()

    def _update_bookmark_icon(self, url: str):
        if self.bookmarks_mgr.is_bookmarked(url):
            self.bookmark_btn.setStyleSheet("color: #00FFAA; font-weight: bold;")
        else:
            self.bookmark_btn.setStyleSheet("color: #94A3B8;")

    def _refresh_bookmarks_bar(self):
        while self.bmk_layout.count():
            child = self.bmk_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        bmks = self.bookmarks_mgr.get_all()
        for b in bmks:
            b_title = b["title"]
            b_url = b["url"]
            btn = QPushButton(b_title)
            btn.setProperty("class", "ActionBtn")
            btn.setStyleSheet("font-size: 12px; padding: 3px 8px;")
            btn.clicked.connect(lambda _, u=b_url: self._navigate_to(u))
            self.bmk_layout.addWidget(btn)
        self.bmk_layout.addStretch()

    def _open_history_dialog(self):
        dlg = HistoryViewerDialog(self.history_mgr, self)
        dlg.open_url_requested.connect(self._navigate_to)
        dlg.exec()

    def _open_downloads_dialog(self):
        dlg = DownloadsDialog(self.downloads_mgr, self)
        dlg.exec()

    def _open_settings_dialog(self):
        dlg = BrowserSettingsDialog(self.search_engine, self.homepage, self.history_mgr, self)
        if dlg.exec():
            self.search_engine = dlg.get_selected_engine()
            self.homepage = dlg.get_homepage()
