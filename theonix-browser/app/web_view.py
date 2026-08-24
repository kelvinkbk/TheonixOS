"""
Theonix Browser — Web View & Page Engine.
Provides Chromium-based QtWebEngine integration, JS content extraction for THAID, and permissions routing.
"""

import os
from typing import Callable
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QMessageBox

HAS_WEBENGINE = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    )
    HAS_WEBENGINE = True
except ImportError:
    pass


class TheonixWebPage(QWebEnginePage if HAS_WEBENGINE else object):
    """Custom WebEngine Page with permission routing and window creation handling."""
    new_tab_requested = pyqtSignal(QUrl)

    def __init__(self, profile=None, parent=None):
        if HAS_WEBENGINE:
            super().__init__(profile, parent)
            self.featurePermissionRequested.connect(self._on_permission_requested)

    def _on_permission_requested(self, security_origin: QUrl, feature):
        # Prompt / manage site permissions
        self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

    def createWindow(self, window_type):
        # Handle target="_blank" or window.open by requesting a new tab in browser
        # Return a temporary page or signal parent
        temp_view = TheonixWebView()
        self.new_tab_requested.emit(QUrl())
        return temp_view.page()


class TheonixWebView(QWebEngineView if HAS_WEBENGINE else QWidget):
    """Main Web View component with Chromium rendering, JS extraction, and devtools."""
    title_updated = pyqtSignal(str)
    url_updated = pyqtSignal(QUrl)
    load_progress_changed = pyqtSignal(int)
    new_window_requested = pyqtSignal(QUrl)

    def __init__(self, profile: 'QWebEngineProfile' = None, parent=None):
        if HAS_WEBENGINE:
            super().__init__(parent)
            self.custom_page = TheonixWebPage(profile or QWebEngineProfile.defaultProfile(), self)
            self.setPage(self.custom_page)

            # Connect core WebEngine signals
            self.titleChanged.connect(self.title_updated)
            self.urlChanged.connect(self.url_updated)
            self.loadProgress.connect(self.load_progress_changed)
            self.custom_page.new_tab_requested.connect(self.new_window_requested)

            # Configure high-performance Chromium settings
            settings = self.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        else:
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.browser = QTextBrowser()
            self.browser.setOpenExternalLinks(True)
            self.browser.setStyleSheet("background-color: #07090E; border: none; color: #F8FAFC; padding: 20px;")
            layout.addWidget(self.browser)
            self._current_url = QUrl("https://duckduckgo.com")

    def load_url(self, url: QUrl):
        if HAS_WEBENGINE:
            self.load(url)
        else:
            self._current_url = url
            self.browser.setHtml(f"<div style='color:white;padding:30px;'><h3>Loading: {url.toString()}</h3><p>Install python-pyqt6-webengine for real Chromium Blink web engine rendering.</p></div>")
            self.url_updated.emit(url)
            self.title_updated.emit(url.host() or "Web Page")
            self.load_progress_changed.emit(100)

    def current_url(self) -> QUrl:
        if HAS_WEBENGINE:
            return self.url()
        return self._current_url

    def extract_page_text(self, callback: Callable[[str], None]):
        """Extracts visible, readable text from the current DOM for THAID AI summarization."""
        if not HAS_WEBENGINE:
            callback(self.browser.toPlainText() if hasattr(self, "browser") else "")
            return

        js_script = """
        (function() {
            let article = document.querySelector('article') || document.querySelector('main') || document.body;
            let text = article ? article.innerText : document.body.innerText;
            return text.substring(0, 8000); // return up to 8k chars for AI
        })();
        """
        self.page().runJavaScript(js_script, callback)

    def extract_selected_text(self, callback: Callable[[str], None]):
        """Extracts user selected text on the web page."""
        if not HAS_WEBENGINE:
            callback("")
            return

        js_script = "window.getSelection().toString();"
        self.page().runJavaScript(js_script, callback)

    def zoom_in(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(min(3.0, self.zoomFactor() + 0.1))

    def zoom_out(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(max(0.25, self.zoomFactor() - 0.1))

    def reset_zoom(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(1.0)
