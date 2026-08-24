#!/usr/bin/env python3
"""
Theonix Store — Ultra-Dark Glassmorphic Software Center & App Discovery Hub
Built for Theonix OS. Unified catalog for Pacman, Flatpak, and UACL apps.
"""

import os
import sqlite3
import subprocess
import sys
import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QProgressBar,
    QScrollArea, QFrame, QStackedWidget, QListWidget, QListWidgetItem,
    QMessageBox, QGridLayout
)

UACL_DB = os.path.expanduser("~/.config/theonix/uacl.db")

THEME_QSS = """
QMainWindow {
    background-color: #07090E;
}

QWidget#CentralWidget {
    background-color: #07090E;
    color: #F8FAFC;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Sidebar Navigation */
QListWidget#CategoryNav {
    background-color: #0E121C;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 14px;
    outline: none;
}

QListWidget#CategoryNav::item {
    color: #94A3B8;
    height: 46px;
    padding-left: 16px;
    margin: 3px 10px;
    border-radius: 10px;
    font-size: 13.5px;
    font-weight: 500;
}

QListWidget#CategoryNav::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
}

QListWidget#CategoryNav::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(108, 99, 255, 0.35), stop:1 rgba(0, 255, 170, 0.25));
    border: 1px solid rgba(0, 255, 170, 0.4);
    color: #FFFFFF;
    font-weight: 600;
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
    background: #0E121C;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #232D42;
    border-radius: 4px;
    min-height: 25px;
}

QScrollBar::handle:vertical:hover {
    background: #384766;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* App Cards */
QFrame.AppCard {
    background-color: rgba(20, 26, 40, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px;
}

QFrame.AppCard:hover {
    border: 1px solid rgba(0, 255, 170, 0.3);
    background-color: rgba(26, 34, 52, 0.9);
}

QFrame.FeaturedHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(108, 99, 255, 0.3), stop:0.5 rgba(18, 26, 44, 0.8), stop:1 rgba(0, 255, 170, 0.15));
    border: 1px solid rgba(0, 255, 170, 0.3);
    border-radius: 16px;
    padding: 24px;
}

/* Search Bar */
QLineEdit#SearchInput {
    background-color: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 18px;
    color: #FFFFFF;
    font-size: 13.5px;
}

QLineEdit#SearchInput:focus {
    border: 1px solid #00FFAA;
    background-color: rgba(18, 24, 38, 0.95);
}

/* Source Badges */
QLabel.BadgePacman {
    background-color: rgba(0, 212, 255, 0.15);
    color: #00D4FF;
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.BadgeFlatpak {
    background-color: rgba(108, 99, 255, 0.2);
    color: #A78BFA;
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel.BadgeUACL {
    background-color: rgba(0, 255, 170, 0.15);
    color: #00FFAA;
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
}

QPushButton.InstallBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    font-weight: 700;
}

QPushButton.InstallBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D75FF, stop:1 #1CE0FF);
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
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(18)

        icon_lbl = QLabel(self.data.get("icon", "📦"))
        icon_lbl.setStyleSheet("font-size: 32px; background: rgba(14, 18, 28, 0.8); border-radius: 12px; padding: 6px;")
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        v_box = QVBoxLayout()
        v_box.setSpacing(4)

        h_title = QHBoxLayout()
        title_lbl = QLabel(self.data["name"])
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        h_title.addWidget(title_lbl)

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
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12.5px;")
        desc_lbl.setWordWrap(True)
        v_box.addWidget(desc_lbl)

        layout.addLayout(v_box, 1)

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
        self.setMinimumSize(1020, 700)
        self.resize(1120, 760)
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
        self.nav_list.setFixedWidth(240)

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
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(18)

        # Top Bar
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
            hero = QFrame()
            hero.setProperty("class", "FeaturedHero")
            h_layout = QVBoxLayout(hero)
            h_layout.setSpacing(8)

            h_title = QLabel("Explore Theonix Ecosystem")
            h_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
            h_desc = QLabel("Discover curated high-performance tools, AI assistants, and native software for Theonix OS.")
            h_desc.setStyleSheet("font-size: 13.5px; color: #94A3B8;")
            h_layout.addWidget(h_title)
            h_layout.addWidget(h_desc)
            self.cards_layout.addWidget(hero)

            hdr = QLabel("Top Community Recommendations")
            hdr.setStyleSheet("font-size: 15px; font-weight: bold; color: #00FFAA; margin-top: 10px;")
            self.cards_layout.addWidget(hdr)

            for app_data in FEATURED_APPS:
                card = AppCard(app_data, self)
                self.cards_layout.addWidget(card)

        elif idx == 6:
            hdr = QLabel("Installed Applications")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)
            lbl = QLabel("To view and launch Windows/UACL and native packages, use the App Manager.")
            lbl.setStyleSheet("color: #94A3B8;")
            self.cards_layout.addWidget(lbl)

        elif idx == 7:
            hdr = QLabel("Pending Software Updates")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)
            
            up_btn = QPushButton("🚀 Launch System Updater")
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
