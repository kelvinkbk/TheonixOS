"""
Theonix Browser — History Viewer Dialog.
"""

from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)

from theonix_core import THEONIX_THEME_QSS, SearchBar


class HistoryViewerDialog(QDialog):
    open_url_requested = pyqtSignal(str)

    def __init__(self, history_mgr, parent=None):
        super().__init__(parent)
        self.history_mgr = history_mgr
        self.setWindowTitle("Browsing History — Theonix Browser")
        self.setMinimumSize(700, 480)
        self.setStyleSheet(THEONIX_THEME_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header with Search
        top_row = QHBoxLayout()
        title = QLabel("📜 Browsing History")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        top_row.addWidget(title)
        top_row.addStretch()

        self.search_bar = SearchBar("Search history...")
        self.search_bar.setFixedWidth(240)
        self.search_bar.textChanged.connect(self._load_entries)
        top_row.addWidget(self.search_bar)

        clear_btn = QPushButton("Clear History")
        clear_btn.setProperty("class", "ActionBtn")
        clear_btn.clicked.connect(self._clear_all)
        top_row.addWidget(clear_btn)
        layout.addLayout(top_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Page Title", "URL", "Visits", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        self._load_entries()

    def _load_entries(self):
        query = self.search_bar.text().strip()
        entries = self.history_mgr.get_recent(limit=100, search_query=query)
        self.table.setRowCount(len(entries))

        for row, item in enumerate(entries):
            ts = datetime.fromtimestamp(item["last_visited"]).strftime("%b %d, %H:%M")
            self.table.setItem(row, 0, QTableWidgetItem(item["title"] or item["url"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["url"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["visit_count"])))
            self.table.setItem(row, 3, QTableWidgetItem(ts))

    def _on_row_double_clicked(self, index):
        row = index.row()
        url_item = self.table.item(row, 1)
        if url_item:
            self.open_url_requested.emit(url_item.text())
            self.accept()

    def _clear_all(self):
        reply = QMessageBox.question(self, "Clear History", "Delete all browsing history records?")
        if reply == QMessageBox.StandardButton.Yes:
            self.history_mgr.clear_all()
            self._load_entries()
