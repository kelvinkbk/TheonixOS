#!/usr/bin/env python3
"""
Theonix Store — Next-Gen Software Center & App Discovery Hub
Built for Theonix OS. Unified catalog for Pacman, Flatpak, and UACL apps.
"""

import os
import sqlite3
import subprocess
import sys
import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QLinearGradient, QBrush, QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QProgressBar,
    QScrollArea, QFrame, QStackedWidget, QListWidget, QListWidgetItem,
    QMessageBox, QGridLayout, QSizePolicy, QTabWidget
)

UACL_DB = os.path.expanduser("~/.config/theonix/uacl.db")

THEME_QSS = """
QMainWindow {
    background-color: #0B0E14;
}

QWidget#CentralWidget {
    background-color: #0B0E14;
    color: #F0F4F8;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Sidebar Navigation */
QListWidget#CategoryNav {
    background-color: #121620;
    border: none;
    border-right: 1px solid #1E2638;
    padding-top: 12px;
    outline: none;
}

QListWidget#CategoryNav::item {
    color: #94A3B8;
    height: 46px;
    padding-left: 18px;
    margin: 3px 10px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
}

QListWidget#CategoryNav::item:hover {
    background-color: rgba(108, 99, 255, 0.12);
    color: #FFFFFF;
}

QListWidget#CategoryNav::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    font-weight: bold;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #121620;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2D3748;
    border-radius: 4px;
    min-height: 25px;
}

QScrollBar::handle:vertical:hover {
    background: #4A5568;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* App Cards */
QFrame.AppCard {
    background-color: #161C28;
    border: 1px solid #232D40;
    border-radius: 12px;
    padding: 14px;
}

QFrame.AppCard:hover {
    border: 1px solid #3B82F6;
    background-color: #19202E;
}

QFrame.FeaturedHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1C1938, stop:0.5 #162035, stop:1 #112826);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px;
}

/* Search Bar */
QLineEdit#SearchInput {
    background-color: #121722;
    border: 1px solid #283347;
    border-radius: 10px;
    padding: 10px 16px;
    color: #F0F4F8;
    font-size: 14px;
}

QLineEdit#SearchInput:focus {
    border: 1px solid #00FFAA;
    background-color: #161D2B;
}

/* Source Badges */
QLabel.BadgePacman {
    background-color: rgba(0, 212, 255, 0.15);
    color: #00D4FF;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.BadgeFlatpak {
    background-color: rgba(108, 99, 255, 0.2);
    color: #A78BFA;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.BadgeUACL {
    background-color: rgba(0, 255, 170, 0.15);
    color: #00FFAA;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: #21293A;
    color: #F0F4F8;
    border: 1px solid #2F3B52;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2D374E;
    border-color: #4B5563;
    color: #FFFFFF;
}

QPushButton.InstallBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    font-weight: bold;
}

QPushButton.InstallBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D75FF, stop:1 #1CE0FF);
}

QPushButton.UninstallBtn {
    background-color: rgba(239, 68, 68, 0.15);
    color: #EF4444;
    border: 1px solid #7F1D1D;
}

QPushButton.UninstallBtn:hover {
    background-color: #EF4444;
    color: #FFFFFF;
}
"""

FEATURED_APPS = [
    {
        "name": "Visual Studio Code",
        "pkg": "code",
        "source": "pacman",
        "category": "Development",
        "icon": "💻",
        "desc": "Powerful, extensible code editor with integrated Git, debugging, and terminal.",
    },
    {
        "name": "Ollama AI Local Engine",
        "pkg": "ollama",
        "source": "pacman",
        "category": "AI & Tools",
        "icon": "🧠",
        "desc": "Run large language models locally and privately on your machine.",
    },
    {
        "name": "Blender 3D",
        "pkg": "blender",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎨",
        "desc": "Free and open-source 3D creation suite supporting modeling, animation, and rendering.",
    },
    {
        "name": "Discord",
        "pkg": "com.discordapp.Discord",
        "source": "flatpak",
        "category": "Communication",
        "icon": "💬",
        "desc": "All-in-one voice and text chat for gamers, communities, and developer teams.",
    },
    {
        "name": "Steam",
        "pkg": "steam",
        "source": "pacman",
        "category": "Gaming",
        "icon": "🎮",
        "desc": "The ultimate online game platform with Proton compatibility for thousands of titles.",
    },
    {
        "name": "LibreOffice Fresh",
        "pkg": "libreoffice-fresh",
        "source": "pacman",
        "category": "Productivity",
        "icon": "📄",
        "desc": "Feature-rich open source office suite including Writer, Calc, and Impress.",
    },
    {
        "name": "GIMP Image Editor",
        "pkg": "gimp",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🖼️",
        "desc": "Advanced photo retouching, image composition, and graphic authoring software.",
    },
    {
        "name": "VLC Media Player",
        "pkg": "vlc",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎬",
        "desc": "Universal media player that plays most multimedia files, discs, and network streams.",
    },
]


class AppCard(QFrame):
    def __init__(self, data: dict, parent_window):
        super().__init__()
        self.data = data
        self.parent_window = parent_window
        self.setProperty("class", "AppCard")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(16)

        # Icon
        icon_lbl = QLabel(self.data.get("icon", "📦"))
        icon_lbl.setStyleSheet("font-size: 32px; background: #121722; border-radius: 10px; padding: 6px;")
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        # Details
        v_box = QVBoxLayout()
        v_box.setSpacing(4)

        h_title = QHBoxLayout()
        title_lbl = QLabel(self.data["name"])
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        h_title.addWidget(title_lbl)

        # Source badge
        src = self.data.get("source", "pacman")
        badge = QLabel(src.upper())
        if src == "pacman":
            badge.setProperty("class", "BadgePacman")
        elif src == "flatpak":
            badge.setProperty("class", "BadgeFlatpak")
        else:
            badge.setProperty("class", "BadgeUACL")
        h_title.addWidget(badge)
        h_title.addStretch()
        v_box.addLayout(h_title)

        desc_lbl = QLabel(self.data.get("desc", "Software package for Theonix OS"))
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        desc_lbl.setWordWrap(True)
        v_box.addWidget(desc_lbl)

        layout.addLayout(v_box, 1)

        # Action Button
        btn = QPushButton("Install")
        btn.setProperty("class", "InstallBtn")
        btn.setFixedWidth(100)
        btn.clicked.connect(self._install_app)
        layout.addWidget(btn)

    def _install_app(self):
        pkg = self.data.get("pkg", self.data["name"])
        src = self.data.get("source", "pacman")

        if src == "pacman":
            subprocess.Popen(["konsole", "-e", "sudo", "pacman", "-S", "--needed", pkg])
        elif src == "flatpak":
            subprocess.Popen(["konsole", "-e", "flatpak", "install", "-y", "flathub", pkg])
        else:
            subprocess.Popen(["theonix-uacl", "launch", "--name", pkg])


class StoreWorker(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query: str, category: str):
        super().__init__()
        self.query = query.strip()
        self.category = category

    def run(self):
        results = []
        if self.query:
            # Search pacman
            try:
                res = subprocess.run(["pacman", "-Ss", self.query], capture_output=True, text=True, timeout=10)
                lines = res.stdout.strip().splitlines()
                cur_pkg = None
                for line in lines:
                    if not line.startswith("    "):
                        parts = line.split()
                        if parts:
                            cur_pkg = parts[0].split("/")[-1]
                            desc = ""
                    else:
                        desc = line.strip()
                        if cur_pkg:
                            results.append({
                                "name": cur_pkg,
                                "pkg": cur_pkg,
                                "source": "pacman",
                                "icon": "📦",
                                "desc": desc
                            })
                            cur_pkg = None
            except Exception:
                pass

            # Search UACL
            if os.path.exists(UACL_DB):
                try:
                    conn = sqlite3.connect(UACL_DB)
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    cur.execute("SELECT name, format_type FROM applications WHERE name LIKE ?", (f"%{self.query}%",))
                    for row in cur.fetchall():
                        results.append({
                            "name": row["name"],
                            "pkg": row["name"],
                            "source": "uacl",
                            "icon": "🪟",
                            "desc": f"Windows/UACL application [{row['format_type']}]"
                        })
                    conn.close()
                except Exception:
                    pass

        self.results_ready.emit(results[:60])


class TheonixStoreWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Store")
        self.setMinimumSize(1000, 700)
        self.resize(1080, 750)
        self.worker = None

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("CategoryNav")
        self.nav_list.setFixedWidth(230)

        categories = [
            "🌟  Featured Picks",
            "💻  Development",
            "🧠  AI & Machine Learning",
            "🎨  Graphics & Media",
            "⚡  Productivity",
            "🎮  Gaming & UACL",
            "📥  Installed Apps",
            "🔄  Updates",
        ]
        for cat in categories:
            self.nav_list.addItem(QListWidgetItem(cat))

        main_layout.addWidget(self.nav_list)

        # Right Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(18)

        # Top Bar (Search + App Manager button)
        top_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search thousands of apps (Pacman, Flatpak, Windows/UACL)...")
        self.search_input.returnPressed.connect(self._trigger_search)

        search_btn = QPushButton("Search")
        search_btn.setProperty("class", "InstallBtn")
        search_btn.clicked.connect(self._trigger_search)

        mgr_btn = QPushButton("App Manager")
        mgr_btn.clicked.connect(lambda: subprocess.Popen(["theonix-app-manager"]))

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(search_btn)
        top_row.addWidget(mgr_btn)
        content_layout.addLayout(top_row)

        # Scrollable Cards Container
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setSpacing(12)
        self.scroll.setWidget(self.scroll_content)
        content_layout.addWidget(self.scroll)

        main_layout.addWidget(content_area, 1)

        self.nav_list.currentRowChanged.connect(self._on_category_changed)
        self.nav_list.setCurrentRow(0)

    def _on_category_changed(self, idx):
        self.search_input.clear()
        self._load_featured_or_category(idx)

    def _load_featured_or_category(self, idx):
        self._clear_cards()

        if idx == 0:
            # Hero Banner
            hero = QFrame()
            hero.setProperty("class", "FeaturedHero")
            h_layout = QVBoxLayout(hero)
            h_layout.setSpacing(8)

            h_title = QLabel("Explore Theonix Ecosystem")
            h_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
            h_desc = QLabel("Discover curated high-performance tools, AI assistants, and native software for Theonix OS.")
            h_desc.setStyleSheet("font-size: 14px; color: #94A3B8;")
            h_layout.addWidget(h_title)
            h_layout.addWidget(h_desc)
            self.cards_layout.addWidget(hero)

            hdr = QLabel("Top Community Recommendations")
            hdr.setStyleSheet("font-size: 16px; font-weight: bold; color: #00FFAA; margin-top: 10px;")
            self.cards_layout.addWidget(hdr)

            for app_data in FEATURED_APPS:
                card = AppCard(app_data, self)
                self.cards_layout.addWidget(card)

        elif idx == 6:  # Installed Apps
            hdr = QLabel("Installed Applications")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)
            lbl = QLabel("To view and launch Windows/UACL and native packages, use the App Manager.")
            lbl.setStyleSheet("color: #94A3B8;")
            self.cards_layout.addWidget(lbl)

        elif idx == 7:  # Updates
            hdr = QLabel("Pending Software Updates")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)
            
            up_btn = QPushButton("🚀  Launch System Updater")
            up_btn.setProperty("class", "InstallBtn")
            up_btn.clicked.connect(lambda: subprocess.Popen(["konsole", "-e", "sudo", "pacman", "-Syu"]))
            self.cards_layout.addWidget(up_btn)

        else:
            cat_name = self.nav_list.item(idx).text().split("  ")[1]
            hdr = QLabel(f"Category: {cat_name}")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)

            filtered = [a for a in FEATURED_APPS if cat_name.lower() in a.get("category", "").lower()]
            for app_data in filtered:
                card = AppCard(app_data, self)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _trigger_search(self):
        query = self.search_input.text().strip()
        if not query:
            self._load_featured_or_category(self.nav_list.currentRow())
            return

        self._clear_cards()
        hdr = QLabel(f"Search Results for '{query}'")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FFAA;")
        self.cards_layout.addWidget(hdr)

        lbl = QLabel("Searching repositories...")
        lbl.setStyleSheet("color: #94A3B8;")
        self.cards_layout.addWidget(lbl)

        self.worker = StoreWorker(query, "all")
        self.worker.results_ready.connect(self._on_search_results)
        self.worker.start()

    def _on_search_results(self, results):
        self._clear_cards()
        query = self.search_input.text().strip()
        hdr = QLabel(f"Search Results for '{query}' ({len(results)} matches)")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FFAA;")
        self.cards_layout.addWidget(hdr)

        if not results:
            none_lbl = QLabel("No packages matched your query.")
            none_lbl.setStyleSheet("color: #94A3B8; font-size: 14px; margin-top: 10px;")
            self.cards_layout.addWidget(none_lbl)
        else:
            for item in results:
                card = AppCard(item, self)
                self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _clear_cards(self):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME_QSS)
    win = TheonixStoreWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
