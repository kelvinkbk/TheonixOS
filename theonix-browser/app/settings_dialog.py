"""
Theonix Browser — Settings & Preferences Dialog.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QCheckBox, QMessageBox, QTabWidget, QWidget
)

from theonix_core import THEONIX_THEME_QSS, GlassCard, Badge


class BrowserSettingsDialog(QDialog):
    SEARCH_ENGINES = {
        "DuckDuckGo": "https://duckduckgo.com/?q={query}",
        "Google": "https://www.google.com/search?q={query}",
        "Startpage": "https://www.startpage.com/sp/search?query={query}",
        "Bing": "https://www.bing.com/search?q={query}",
    }

    def __init__(self, current_search: str, current_home: str, history_mgr, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Theonix Browser Settings")
        self.setMinimumSize(540, 420)
        self.setStyleSheet(THEONIX_THEME_QSS)
        self.history_mgr = history_mgr

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("⚙️ Browser Preferences")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        # General Card
        gen_card = GlassCard()
        g_layout = QVBoxLayout(gen_card)
        g_layout.setSpacing(12)

        g_hdr = QLabel("Search Engine & Homepage")
        g_hdr.setStyleSheet("color: #00FFAA; font-weight: bold; font-size: 13px;")
        g_layout.addWidget(g_hdr)

        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("Default Search Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(list(self.SEARCH_ENGINES.keys()))
        if current_search in self.SEARCH_ENGINES:
            self.engine_combo.setCurrentText(current_search)
        s_row.addWidget(self.engine_combo)
        g_layout.addLayout(s_row)

        h_row = QHBoxLayout()
        h_row.addWidget(QLabel("Homepage URL:"))
        self.home_input = QLineEdit()
        self.home_input.setText(current_home or "https://duckduckgo.com")
        h_row.addWidget(self.home_input)
        g_layout.addLayout(h_row)

        layout.addWidget(gen_card)

        # Privacy Card
        priv_card = GlassCard()
        p_layout = QVBoxLayout(priv_card)
        p_layout.setSpacing(10)

        p_hdr = QLabel("Privacy & Data")
        p_hdr.setStyleSheet("color: #00FFAA; font-weight: bold; font-size: 13px;")
        p_layout.addWidget(p_hdr)

        self.block_trackers = QCheckBox("Enable Tracking & Fingerprint Protection")
        self.block_trackers.setChecked(True)
        self.https_only = QCheckBox("Enforce HTTPS-Only Mode")
        self.https_only.setChecked(True)
        p_layout.addWidget(self.block_trackers)
        p_layout.addWidget(self.https_only)

        clear_btn = QPushButton("Clear Browsing History & Cache")
        clear_btn.setProperty("class", "ActionBtn")
        clear_btn.clicked.connect(self._clear_history)
        p_layout.addWidget(clear_btn)

        layout.addWidget(priv_card)
        layout.addStretch()

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Cancel")
        close_btn.setProperty("class", "ActionBtn")
        close_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Settings")
        save_btn.setProperty("class", "PrimaryBtn")
        save_btn.clicked.connect(self.accept)

        btn_row.addWidget(close_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _clear_history(self):
        reply = QMessageBox.question(self, "Clear History", "Clear all recorded browsing history?")
        if reply == QMessageBox.StandardButton.Yes:
            self.history_mgr.clear_all()
            QMessageBox.information(self, "History", "Browsing history successfully cleared.")

    def get_selected_engine(self) -> str:
        return self.engine_combo.currentText()

    def get_homepage(self) -> str:
        return self.home_input.text().strip()
