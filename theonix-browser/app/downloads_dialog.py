"""
Theonix Browser — Downloads Dialog.
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QWidget, QFrame
)

from theonix_core import THEONIX_THEME_QSS, GlassCard, Badge


class DownloadCard(GlassCard):
    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.item = download_item

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: filename + status badge
        top_row = QHBoxLayout()
        name_lbl = QLabel(f"📄  {self.item.filename}")
        name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        top_row.addWidget(name_lbl)
        top_row.addStretch()

        self.status_badge = Badge("DOWNLOADING", "cyan")
        top_row.addWidget(self.status_badge)
        layout.addLayout(top_row)

        # Progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        layout.addWidget(self.bar)

        # Details + Action buttons
        bot_row = QHBoxLayout()
        self.detail_lbl = QLabel("0 KB / 0 KB")
        self.detail_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        bot_row.addWidget(self.detail_lbl)
        bot_row.addStretch()

        self.open_btn = QPushButton("Open File")
        self.open_btn.setProperty("class", "PrimaryBtn")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.item.open_file)

        self.show_folder_btn = QPushButton("Show in Files")
        self.show_folder_btn.setProperty("class", "ActionBtn")
        self.show_folder_btn.clicked.connect(self.item.show_in_files)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "ActionBtn")
        self.cancel_btn.clicked.connect(self.item.cancel)

        bot_row.addWidget(self.open_btn)
        bot_row.addWidget(self.show_folder_btn)
        bot_row.addWidget(self.cancel_btn)
        layout.addLayout(bot_row)

        self.item.progress_changed.connect(self._on_progress)
        self.item.status_changed.connect(self._on_status)

    def _on_progress(self, rec: int, total: int):
        if total > 0:
            pct = int((rec / total) * 100)
            self.bar.setValue(pct)
            rec_mb = rec / (1024**2)
            total_mb = total / (1024**2)
            self.detail_lbl.setText(f"{rec_mb:.1f} MB / {total_mb:.1f} MB ({pct}%)")
        else:
            rec_mb = rec / (1024**2)
            self.detail_lbl.setText(f"{rec_mb:.1f} MB downloaded")

    def _on_status(self, status: str):
        if status == "completed":
            self.status_badge.setText("COMPLETED")
            self.status_badge.setStyleSheet("background: rgba(0,255,170,0.15); color: #00FFAA; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
            self.bar.setValue(100)
            self.open_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
        elif status == "cancelled":
            self.status_badge.setText("CANCELLED")
            self.status_badge.setStyleSheet("background: rgba(255,95,86,0.15); color: #FF5F56; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
            self.cancel_btn.setVisible(False)


class DownloadsDialog(QDialog):
    def __init__(self, downloads_mgr, parent=None):
        super().__init__(parent)
        self.downloads_mgr = downloads_mgr
        self.setWindowTitle("Downloads — Theonix Browser")
        self.setMinimumSize(640, 440)
        self.setStyleSheet(THEONIX_THEME_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("📥 Download Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        hdr.addWidget(title)
        hdr.addStretch()

        open_folder_btn = QPushButton("Open Downloads Folder")
        open_folder_btn.setProperty("class", "ActionBtn")
        open_folder_btn.clicked.connect(lambda: os.system("theonix-files ~/Downloads &") if os.path.exists(os.path.expanduser("~/Downloads")) else None)
        hdr.addWidget(open_folder_btn)
        layout.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(scroll_content)
        self.cards_layout.setSpacing(10)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        if not self.downloads_mgr.downloads:
            empty_lbl = QLabel("No active or recent downloads.")
            empty_lbl.setStyleSheet("color: #94A3B8; padding: 40px; text-align: center;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_lbl)
        else:
            for item in self.downloads_mgr.downloads:
                card = DownloadCard(item)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()
