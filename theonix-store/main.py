#!/usr/bin/env python3
"""
Theonix Store — Unified Software Center & App Marketplace for Theonix OS.
Powered by theonix_core platform services with 'Run on Theonix' compatibility rating.
"""

import os
import sqlite3
import subprocess
import sys
import threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")))

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QProgressBar,
    QScrollArea, QFrame, QStackedWidget, QMessageBox, QGridLayout,
    QButtonGroup, QDialog, QTextEdit
)

from theonix_core import (
    THEONIX_THEME_QSS, GlassCard, NavButton, Badge,
    SearchBar, apply_theonix_style,
    PackageService, CompatibilityRating, UACLService
)

FEATURED_APPS = [
    {
        "name": "Visual Studio Code",
        "pkg": "code",
        "source": "pacman",
        "category": "Development",
        "icon": "💻",
        "version": "1.92.0",
        "size": "95 MB",
        "desc": "Industry-leading extensible code editor with integrated debugging, Git, and terminal.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Official Arch Linux native binary (100% performance)"
    },
    {
        "name": "Ollama AI Local Engine",
        "pkg": "ollama",
        "source": "pacman",
        "category": "AI & Tools",
        "icon": "🧠",
        "version": "0.3.12",
        "size": "32 MB",
        "desc": "Run large neural models locally on your GPU/CPU with full privacy and zero cloud telemetry.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Hardware accelerated native inference engine"
    },
    {
        "name": "Blender 3D Suite",
        "pkg": "blender",
        "source": "pacman",
        "category": "Graphics",
        "icon": "🎨",
        "version": "4.2.1",
        "size": "240 MB",
        "desc": "Comprehensive 3D creation suite: modeling, sculpting, VFX, animation, and Cycles rendering.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Vulkan & OptiX accelerated native Linux package"
    },
    {
        "name": "Discord",
        "pkg": "com.discordapp.Discord",
        "source": "flatpak",
        "category": "Communication",
        "icon": "💬",
        "version": "0.0.60",
        "size": "85 MB",
        "desc": "Voice, video, and text communication service for gaming, developers, and communities.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed Flathub container with PipeWire audio"
    },
    {
        "name": "Steam & Proton",
        "pkg": "steam",
        "source": "pacman",
        "category": "Games",
        "icon": "🎮",
        "version": "1.0.0.79",
        "size": "65 MB",
        "desc": "The ultimate gaming platform with Proton DXVK/VKD3D compatibility for thousands of titles.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native client with Vulkan translation layers"
    },
    {
        "name": "Notepad++ (Win32)",
        "pkg": "npp.installer.exe",
        "source": "uacl",
        "category": "Utilities",
        "icon": "🪟",
        "version": "8.6.9",
        "size": "15 MB",
        "desc": "Classic lightweight Win32 source code editor running through Theonix UACL.",
        "compat": CompatibilityRating.UACL_COMPATIBLE,
        "compat_desc": "Windows binary managed seamlessly by Theonix UACL"
    },
    {
        "name": "GIMP Image Editor",
        "pkg": "gimp",
        "source": "pacman",
        "category": "Graphics",
        "icon": "🖼️",
        "version": "2.10.38",
        "size": "115 MB",
        "desc": "Advanced photo retouching, image composition, and graphic design authoring software.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Official Arch Linux native application"
    },
    {
        "name": "VLC Media Player",
        "pkg": "vlc",
        "source": "pacman",
        "category": "Multimedia",
        "icon": "🎬",
        "version": "3.0.21",
        "size": "45 MB",
        "desc": "Universal media player that plays most multimedia files, codecs, and network streams.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "High performance PipeWire and VAAPI accelerated"
    },
]


class AppDetailDialog(QDialog):
    def __init__(self, app_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{app_data['name']} — Details")
        self.setMinimumSize(560, 420)
        self.setStyleSheet(THEONIX_THEME_QSS)

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
        
        compat_val = app_data.get("compat", CompatibilityRating.NATIVE)
        if compat_val == CompatibilityRating.NATIVE:
            compat_badge = Badge("🟢 NATIVE LINUX", "green")
        elif compat_val == CompatibilityRating.UACL_COMPATIBLE:
            compat_badge = Badge("🟢 WORKS WITH UACL", "cyan")
        elif compat_val == CompatibilityRating.CONFIG_REQUIRED:
            compat_badge = Badge("🟡 CONFIG REQUIRED", "yellow")
        else:
            compat_badge = Badge("🔴 UNSUPPORTED", "red")

        h_badge_row = QHBoxLayout()
        h_badge_row.addWidget(compat_badge)
        h_badge_row.addWidget(QLabel(f"Source: {app_data.get('source', 'pacman').upper()}"))
        h_badge_row.addStretch()

        title_box.addWidget(name)
        title_box.addLayout(h_badge_row)
        top_row.addLayout(title_box)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Description
        desc_card = GlassCard()
        d_layout = QVBoxLayout(desc_card)
        desc_text = QLabel(app_data.get("desc", "No description provided."))
        desc_text.setStyleSheet("color: #F8FAFC; font-size: 13.5px; line-height: 1.5;")
        desc_text.setWordWrap(True)
        d_layout.addWidget(desc_text)

        compat_note = QLabel(f"<b>Run on Theonix:</b> {app_data.get('compat_desc', 'Tested and verified.')}")
        compat_note.setStyleSheet("color: #00FFAA; font-size: 12px; margin-top: 6px;")
        d_layout.addWidget(compat_note)

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
        install_btn.setProperty("class", "PrimaryBtn")
        install_btn.clicked.connect(lambda: self._install(app_data))

        btn_row.addWidget(close_btn)
        btn_row.addWidget(install_btn)
        layout.addLayout(btn_row)

    def _install(self, data):
        self.accept()
        dlg = AppInstallDialog(data, self.parent_window)
        dlg.exec()


class PackageInstallWorker(QThread):
    log_received = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, pkg: str, source: str = "pacman"):
        super().__init__()
        self.pkg = pkg
        self.source = source

    def run(self):
        if self.source == "pacman":
            # Use pkexec for native GUI polkit authentication (no terminal needed)
            cmd = ["pkexec", "pacman", "-S", "--needed", "--noconfirm", self.pkg]
        elif self.source == "flatpak":
            # User-level flatpak installs without requiring root permissions
            cmd = ["flatpak", "install", "-y", "--user", "flathub", self.pkg]
        else:
            self.log_received.emit(f"Launching UACL Compatibility layer for {self.pkg}...\n")
            UACLService.launch(self.pkg)
            self.finished.emit(True, "Launched with UACL.")
            return

        try:
            self.log_received.emit(f"⚡ Starting package installation: {self.pkg}\n")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.log_received.emit(line)
            proc.wait()
            if proc.returncode == 0:
                self.finished.emit(True, f"✓ Successfully installed {self.pkg}!")
            else:
                self.finished.emit(False, f"Installation ended with code {proc.returncode}")
        except Exception as e:
            self.finished.emit(False, f"Installation error: {e}")


class AppInstallDialog(QDialog):
    """Modern Glassmorphic In-App Package Installer Dialog."""
    def __init__(self, app_data: dict, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.setWindowTitle(f"Installing {app_data['name']}")
        self.setMinimumSize(480, 360)
        self.setStyleSheet("""
            QDialog { background-color: #0B0E17; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px; }
            QLabel { color: #F8FAFC; }
            QTextEdit { background-color: #07090E; border: 1px solid #1E2638; border-radius: 8px; color: #00FFAA; font-family: monospace; font-size: 11.5px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        icon = QLabel(app_data.get("icon", "📦"))
        icon.setStyleSheet("font-size: 32px;")
        hdr.addWidget(icon)

        t_box = QVBoxLayout()
        self.title_lbl = QLabel(f"Installing {app_data['name']}...")
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        self.status_lbl = QLabel("Downloading packages & verifying signatures...")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12.5px;")
        t_box.addWidget(self.title_lbl)
        t_box.addWidget(self.status_lbl)
        hdr.addLayout(t_box)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate pulsating
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #121826; border-radius: 3px; border: none; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00FFAA); border-radius: 3px; }
        """)
        layout.addWidget(self.progress_bar)

        # Live log output
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)

        # Actions
        self.btn_row = QHBoxLayout()
        self.btn_row.addStretch()

        self.launch_btn = QPushButton("🚀 Launch App")
        self.launch_btn.setProperty("class", "PrimaryBtn")
        self.launch_btn.setVisible(False)
        self.launch_btn.clicked.connect(self._launch_installed_app)

        self.close_btn = QPushButton("Cancel")
        self.close_btn.setProperty("class", "ActionBtn")
        self.close_btn.clicked.connect(self.reject)

        self.btn_row.addWidget(self.launch_btn)
        self.btn_row.addWidget(self.close_btn)
        layout.addLayout(self.btn_row)

        # Start background installation
        pkg = app_data.get("pkg", app_data["name"])
        src = app_data.get("source", "pacman")
        self.worker = PackageInstallWorker(pkg, src)
        self.worker.log_received.connect(self._on_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_log(self, text: str):
        self.log_view.append(text.strip())

    def _on_finished(self, success: bool, msg: str):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.close_btn.setText("Close")
        if success:
            self.title_lbl.setText(f"✓ {self.app_data['name']} Ready!")
            self.status_lbl.setText("Installation completed successfully.")
            self.status_lbl.setStyleSheet("color: #00FFAA; font-weight: bold;")
            self.launch_btn.setVisible(True)
        else:
            self.title_lbl.setText("Installation Incomplete")
            self.status_lbl.setText(msg)
            self.status_lbl.setStyleSheet("color: #FF5555;")

    def _launch_installed_app(self):
        pkg = self.app_data.get("pkg", self.app_data["name"])
        subprocess.Popen([pkg], stderr=subprocess.DEVNULL)
        self.accept()


class AppCard(GlassCard):
    def __init__(self, data: dict, parent_window):
        super().__init__()
        self.data = data
        self.parent_window = parent_window
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

        compat_val = self.data.get("compat", CompatibilityRating.NATIVE)
        if compat_val == CompatibilityRating.NATIVE:
            badge = Badge("NATIVE", "green")
        elif compat_val == CompatibilityRating.UACL_COMPATIBLE:
            badge = Badge("UACL", "cyan")
        else:
            badge = Badge("CONFIG", "yellow")

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
        btn.setProperty("class", "PrimaryBtn")
        btn.setFixedWidth(90)
        btn.clicked.connect(self._install_app)
        layout.addWidget(btn)

    def _open_details(self):
        dlg = AppDetailDialog(self.data, self.parent_window)
        dlg.exec()

    def _install_app(self):
        dlg = AppInstallDialog(self.data, self.parent_window)
        dlg.exec()


class StoreWorker(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        results = PackageService.search_packages(self.query)
        self.results_ready.emit(results)


class TheonixStoreWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Store")
        self.setMinimumSize(1020, 700)
        self.resize(1140, 760)
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
        brand_tag = Badge("STORE", "indigo")
        
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
            btn = NavButton(cat)
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
        self.search_input = SearchBar("Search thousands of packages, Flatpaks, and UACL Windows apps...")
        self.search_input.returnPressed.connect(self._trigger_search)

        search_btn = QPushButton("Search")
        search_btn.setProperty("class", "PrimaryBtn")
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

        filter_options = [
            ("All Sources", "all"),
            ("🟢 Native Linux", "pacman"),
            ("🟣 Flatpaks", "flatpak"),
            ("🪟 Windows / UACL", "uacl")
        ]
        for c_idx, (c_label, c_id) in enumerate(filter_options):
            chip = QPushButton(c_label)
            chip.setProperty("class", "ActionBtn")
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
            hero = GlassCard()
            hero.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(108, 99, 255, 0.3), stop:0.5 rgba(18, 26, 44, 0.8), stop:1 rgba(0, 255, 170, 0.15)); border: 1px solid rgba(0, 255, 170, 0.3); border-radius: 16px; padding: 24px;")
            h_layout = QVBoxLayout(hero)
            h_layout.setSpacing(8)

            h_title = QLabel("Explore Theonix Ecosystem")
            h_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
            h_desc = QLabel("Discover curated native packages, sandboxed Flatpaks, and automated Windows apps running through Theonix UACL.")
            h_desc.setStyleSheet("font-size: 13.5px; color: #94A3B8;")
            h_layout.addWidget(h_title)
            h_layout.addWidget(h_desc)
            self.cards_layout.addWidget(hero)

            hdr = QLabel("Top Recommended Applications")
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
            up_btn.setProperty("class", "PrimaryBtn")
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

        self.worker = StoreWorker(query)
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
    apply_theonix_style(app)
    win = TheonixStoreWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
