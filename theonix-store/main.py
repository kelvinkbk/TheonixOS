#!/usr/bin/env python3
"""
Theonix Store — Ultra-Dark Glassmorphic Software Center & App Discovery Hub
Built for Theonix OS. Unified catalog for Pacman, Flatpak, and UACL apps.
Features app detail cards, multi-source backend filtering, and package management.
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
    QScrollArea, QFrame, QStackedWidget, QMessageBox, QGridLayout,
    QButtonGroup, QDialog, QTextEdit
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

/* Sidebar Container */
QWidget#SidebarContainer {
    background-color: #0B0E17;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Sidebar Navigation Buttons */
QPushButton.NavBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13.5px;
    font-weight: 500;
    text-align: left;
    margin: 2px 10px;
}

QPushButton.NavBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #FFFFFF;
}

QPushButton.NavBtn:checked {
    background-color: rgba(108, 99, 255, 0.2);
    border-left: 3px solid #00FFAA;
    color: #FFFFFF;
    font-weight: 700;
}

/* Filter Chips */
QPushButton.FilterChip {
    background-color: rgba(255, 255, 255, 0.06);
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QPushButton.FilterChip:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #FFFFFF;
}

QPushButton.FilterChip:checked {
    background: linear-gradient(135deg, rgba(108, 99, 255, 0.4), rgba(0, 255, 170, 0.3));
    border: 1px solid #00FFAA;
    color: #FFFFFF;
    font-weight: 700;
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
    background: #0B0E17;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #232D42;
    border-radius: 3px;
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
    background-color: rgba(18, 24, 38, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 16px;
}

QFrame.AppCard:hover {
    border: 1px solid rgba(0, 255, 170, 0.3);
    background-color: rgba(24, 32, 50, 0.85);
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
QPushButton.ActionBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.ActionBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
}

QPushButton.InstallBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    padding: 8px 16px;
    font-size: 13px;
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
        "version": "1.92.0",
        "size": "95 MB",
        "desc": "Powerful, extensible code editor with integrated Git, debugging, and terminal.",
    },
    {
        "name": "Ollama AI Local Engine",
        "pkg": "ollama",
        "source": "pacman",
        "category": "AI & Tools",
        "icon": "🧠",
        "version": "0.3.12",
        "size": "32 MB",
        "desc": "Run large language models locally and privately on your machine with GPU support.",
    },
    {
        "name": "Blender 3D",
        "pkg": "blender",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎨",
        "version": "4.2.1",
        "size": "240 MB",
        "desc": "Free and open-source 3D creation suite supporting modeling, animation, and rendering.",
    },
    {
        "name": "Discord",
        "pkg": "com.discordapp.Discord",
        "source": "flatpak",
        "category": "Communication",
        "icon": "💬",
        "version": "0.0.60",
        "size": "85 MB",
        "desc": "All-in-one voice and text chat for gamers, communities, and developer teams.",
    },
    {
        "name": "Steam",
        "pkg": "steam",
        "source": "pacman",
        "category": "Gaming",
        "icon": "🎮",
        "version": "1.0.0.79",
        "size": "65 MB",
        "desc": "The ultimate online game platform with Proton compatibility for thousands of titles.",
    },
    {
        "name": "LibreOffice Fresh",
        "pkg": "libreoffice-fresh",
        "source": "pacman",
        "category": "Productivity",
        "icon": "📄",
        "version": "24.8.0",
        "size": "180 MB",
        "desc": "Feature-rich open source office suite including Writer, Calc, and Impress.",
    },
    {
        "name": "GIMP Image Editor",
        "pkg": "gimp",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🖼️",
        "version": "2.10.38",
        "size": "115 MB",
        "desc": "Advanced photo retouching, image composition, and graphic authoring software.",
    },
    {
        "name": "VLC Media Player",
        "pkg": "vlc",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎬",
        "version": "3.0.21",
        "size": "45 MB",
        "desc": "Universal media player that plays most multimedia files, discs, and network streams.",
    },
]


class AppDetailDialog(QDialog):
    def __init__(self, app_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{app_data['name']} — Details")
        self.setMinimumSize(540, 380)
        self.setStyleSheet(THEME_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        top_row = QHBoxLayout()
        icon = QLabel(app_data.get("icon", "📦"))
        icon.setStyleSheet("font-size: 40px; background: rgba(14, 18, 28, 0.9); border-radius: 14px; padding: 8px;")
        icon.setFixedSize(60, 60)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(icon)

        title_box = QVBoxLayout()
        name = QLabel(app_data["name"])
        name.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF;")
        pkg = QLabel(f"Package: {app_data.get('pkg', app_data['name'])} · {app_data.get('source', 'pacman').upper()}")
        pkg.setStyleSheet("color: #00FFAA; font-size: 12.5px; font-weight: bold;")
        title_box.addWidget(name)
        title_box.addWidget(pkg)
        top_row.addLayout(title_box)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Description
        desc_card = QFrame()
        desc_card.setProperty("class", "AppCard")
        d_layout = QVBoxLayout(desc_card)
        desc_text = QLabel(app_data.get("desc", "No description provided."))
        desc_text.setStyleSheet("color: #F8FAFC; font-size: 13.5px; line-height: 1.5;")
        desc_text.setWordWrap(True)
        d_layout.addWidget(desc_text)

        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel(f"<b>Version:</b> {app_data.get('version', '1.0')}"))
        meta_row.addWidget(QLabel(f"<b>Size:</b> {app_data.get('size', 'Standard')}"))
        meta_row.addWidget(QLabel("<b>License:</b> GPL / MIT"))
        meta_row.addStretch()
        d_layout.addLayout(meta_row)
        layout.addWidget(desc_card)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "ActionBtn")
        close_btn.clicked.connect(self.accept)
        
        install_btn = QPushButton("Install Package")
        install_btn.setProperty("class", "InstallBtn")
        install_btn.clicked.connect(lambda: self._install(app_data))

        btn_row.addWidget(close_btn)
        btn_row.addWidget(install_btn)
        layout.addLayout(btn_row)

    def _install(self, data):
        self.accept()
        pkg = data.get("pkg", data["name"])
        src = data.get("source", "pacman")
        if src == "pacman":
            subprocess.Popen(["konsole", "-e", "sudo", "pacman", "-S", "--needed", pkg])
        elif src == "flatpak":
            subprocess.Popen(["konsole", "-e", "flatpak", "install", "-y", "flathub", pkg])
        else:
            subprocess.Popen(["theonix-uacl", "launch", "--name", pkg])


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
        icon_lbl.setStyleSheet("font-size: 30px; background: rgba(14, 18, 28, 0.8); border-radius: 12px; padding: 6px;")
        icon_lbl.setFixedSize(48, 48)
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

        details_btn = QPushButton("Details")
        details_btn.setProperty("class", "ActionBtn")
        details_btn.clicked.connect(self._open_details)
        layout.addWidget(details_btn)

        btn = QPushButton("Install")
        btn.setProperty("class", "InstallBtn")
        btn.setFixedWidth(90)
        btn.clicked.connect(self._install_app)
        layout.addWidget(btn)

    def _open_details(self):
        dlg = AppDetailDialog(self.data, self.parent_window)
        dlg.exec()

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
        self.active_filter = "all"

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Container
        sidebar_box = QWidget()
        sidebar_box.setObjectName("SidebarContainer")
        sidebar_box.setFixedWidth(250)
        sb_layout = QVBoxLayout(sidebar_box)
        sb_layout.setContentsMargins(0, 18, 0, 18)
        sb_layout.setSpacing(4)

        # Brand header
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(20, 0, 20, 14)
        brand_icon = QLabel("🛍️")
        brand_icon.setStyleSheet("font-size: 18px;")
        brand_title = QLabel("THEONIX")
        brand_title.setStyleSheet("font-size: 14px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;")
        brand_tag = QLabel("STORE")
        brand_tag.setStyleSheet("font-size: 10.5px; font-weight: bold; background: rgba(108,99,255,0.2); color: #A78BFA; padding: 2px 6px; border-radius: 4px;")
        
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title)
        brand_row.addWidget(brand_tag)
        brand_row.addStretch()
        sb_layout.addLayout(brand_row)

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

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for idx, cat in enumerate(categories):
            btn = QPushButton(cat)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_group.addButton(btn, idx)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()
        main_layout.addWidget(sidebar_box)

        # Right Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(16)

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
        mgr_btn.setProperty("class", "ActionBtn")
        mgr_btn.clicked.connect(lambda: subprocess.Popen(["theonix-app-manager"]))

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(search_btn)
        top_row.addWidget(mgr_btn)
        content_layout.addLayout(top_row)

        # Backend Filter Chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        filter_options = [("All Sources", "all"), ("📦 Pacman / Arch", "pacman"), ("🟣 Flatpak", "flatpak"), ("🪟 Windows / UACL", "uacl")]
        for c_idx, (c_label, c_id) in enumerate(filter_options):
            chip = QPushButton(c_label)
            chip.setProperty("class", "FilterChip")
            chip.setCheckable(True)
            self.chip_group.addButton(chip, c_idx)
            chips_row.addWidget(chip)

        chips_row.addStretch()
        content_layout.addLayout(chips_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setSpacing(12)
        self.scroll.setWidget(self.scroll_content)
        content_layout.addWidget(self.scroll)

        main_layout.addWidget(content_area, 1)

        self.btn_group.idClicked.connect(self._on_category_changed)
        self.chip_group.idClicked.connect(self._on_filter_changed)

        first_btn = self.btn_group.button(0)
        if first_btn:
            first_btn.setChecked(True)
        first_chip = self.chip_group.button(0)
        if first_chip:
            first_chip.setChecked(True)

        self._load_featured_or_category(0)

    def _on_filter_changed(self, idx):
        filters = ["all", "pacman", "flatpak", "uacl"]
        self.active_filter = filters[idx] if idx < len(filters) else "all"
        query = self.search_input.text().strip()
        if query:
            self._trigger_search()
        else:
            self._load_featured_or_category(self.btn_group.checkedId())

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
                if self.active_filter == "all" or app_data.get("source") == self.active_filter:
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
            cat_name = self.btn_group.button(idx).text().split("  ")[1]
            hdr = QLabel(f"Category: {cat_name}")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)

            filtered = [a for a in FEATURED_APPS if cat_name.lower() in a.get("category", "").lower()]
            for app_data in filtered:
                if self.active_filter == "all" or app_data.get("source") == self.active_filter:
                    card = AppCard(app_data, self)
                    self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _trigger_search(self):
        query = self.search_input.text().strip()
        if not query:
            checked_btn = self.btn_group.checkedId()
            self._load_featured_or_category(checked_btn if checked_btn >= 0 else 0)
            return

        self._clear_cards()
        hdr = QLabel(f"Search Results for '{query}'")
        hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FFAA;")
        self.cards_layout.addWidget(hdr)

        lbl = QLabel("Searching repositories...")
        lbl.setStyleSheet("color: #94A3B8;")
        self.cards_layout.addWidget(lbl)

        self.worker = StoreWorker(query, self.active_filter)
        self.worker.results_ready.connect(self._on_search_results)
        self.worker.start()

    def _on_search_results(self, results):
        self._clear_cards()
        query = self.search_input.text().strip()
        
        if self.active_filter != "all":
            results = [r for r in results if r.get("source") == self.active_filter]

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
    app.setStyle("Fusion")
    app.setStyleSheet(THEME_QSS)
    win = TheonixStoreWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
