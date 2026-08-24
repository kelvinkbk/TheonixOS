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
    # Development
    {
        "name": "Visual Studio Code",
        "pkg": "code",
        "source": "pacman",
        "category": "Development",
        "icon": "💻",
        "version": "1.92.0",
        "size": "95 MB",
        "desc": "Industry-standard code editor with built-in debugging, Git, extensions, and terminal.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Official Arch Linux native package (100% performance)"
    },
    {
        "name": "PyCharm Community",
        "pkg": "pycharm-community-edition",
        "source": "pacman",
        "category": "Development",
        "icon": "🐍",
        "version": "2024.2",
        "size": "480 MB",
        "desc": "Intelligent Python IDE with smart code inspection, refactoring, and debugger.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux Java/JVM IDE"
    },
    {
        "name": "Neovim",
        "pkg": "neovim",
        "source": "pacman",
        "category": "Development",
        "icon": "⌨️",
        "version": "0.10.1",
        "size": "18 MB",
        "desc": "Hyperextensible Vim-based modal text editor with Lua plugin architecture and LSP.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Ultra-fast native C binary"
    },
    {
        "name": "Godot Engine 4",
        "pkg": "godot",
        "source": "pacman",
        "category": "Development",
        "icon": "🤖",
        "version": "4.3.0",
        "size": "85 MB",
        "desc": "Free and open-source 2D and 3D cross-platform game engine with Vulkan renderer.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Vulkan accelerated native game engine"
    },
    {
        "name": "GitKraken Git GUI",
        "pkg": "com.axosoft.GitKraken",
        "source": "flatpak",
        "category": "Development",
        "icon": "🐙",
        "version": "10.1.0",
        "size": "110 MB",
        "desc": "Visual Git client with interactive merge conflict resolver and worktree management.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed Flathub container"
    },
    {
        "name": "DBeaver Database Tool",
        "pkg": "dbeaver",
        "source": "pacman",
        "category": "Development",
        "icon": "🗄️",
        "version": "24.1.5",
        "size": "98 MB",
        "desc": "Universal database manager for PostgreSQL, MySQL, SQLite, Oracle, and Redis.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux database IDE"
    },

    # AI & Machine Learning
    {
        "name": "THAID AI Assistant",
        "pkg": "thaid-gui",
        "source": "pacman",
        "category": "AI & Machine Learning",
        "icon": "✨",
        "version": "2.0.0",
        "size": "12 MB",
        "desc": "Theonix OS system-level neural assistant for autonomous control, code generation, and browsing.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Built-in Theonix OS core service"
    },
    {
        "name": "Ollama AI Local Engine",
        "pkg": "ollama",
        "source": "pacman",
        "category": "AI & Machine Learning",
        "icon": "🧠",
        "version": "0.3.12",
        "size": "32 MB",
        "desc": "Run large language models locally on CPU/GPU with zero cloud telemetry.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Hardware accelerated native inference engine"
    },
    {
        "name": "LM Studio",
        "pkg": "ai.lmstudio.LMStudio",
        "source": "flatpak",
        "category": "AI & Machine Learning",
        "icon": "🔮",
        "version": "0.3.2",
        "size": "140 MB",
        "desc": "Discover, download, and experiment with local LLMs with a rich chat and API interface.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed container with CUDA/ROCm offload"
    },
    {
        "name": "Whisper Speech-to-Text",
        "pkg": "openai-whisper",
        "source": "pacman",
        "category": "AI & Machine Learning",
        "icon": "🎙️",
        "version": "20231117",
        "size": "45 MB",
        "desc": "High-accuracy neural voice transcription and multi-language translation model.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "PyTorch accelerated audio model"
    },

    # Graphics & Media
    {
        "name": "Blender 3D Suite",
        "pkg": "blender",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎨",
        "version": "4.2.1",
        "size": "240 MB",
        "desc": "Comprehensive 3D creation suite: modeling, sculpting, VFX, animation, and Cycles rendering.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Vulkan & OptiX accelerated native Linux package"
    },
    {
        "name": "GIMP Image Editor",
        "pkg": "gimp",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🖼️",
        "version": "2.10.38",
        "size": "115 MB",
        "desc": "Advanced photo retouching, image composition, and graphic design authoring software.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Official Arch Linux native application"
    },
    {
        "name": "Krita Digital Painting",
        "pkg": "krita",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🖌️",
        "version": "5.2.3",
        "size": "180 MB",
        "desc": "Professional painting program for concept artists, illustrators, and matte painters.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Qt6 Wayland native creative application"
    },
    {
        "name": "Inkscape Vector Studio",
        "pkg": "inkscape",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "📐",
        "version": "1.3.2",
        "size": "130 MB",
        "desc": "Professional vector graphics editor for SVG illustration, typography, and iconography.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux vector suite"
    },
    {
        "name": "OBS Studio",
        "pkg": "obs-studio",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "📹",
        "version": "30.2.2",
        "size": "60 MB",
        "desc": "Live streaming and screen video recording with PipeWire capture and NVENC/VAAPI.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Hardware encoder accelerated"
    },
    {
        "name": "VLC Media Player",
        "pkg": "vlc",
        "source": "pacman",
        "category": "Graphics & Media",
        "icon": "🎬",
        "version": "3.0.21",
        "size": "45 MB",
        "desc": "Universal media player that plays most multimedia files, codecs, and network streams.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "High performance PipeWire and VAAPI accelerated"
    },

    # Productivity
    {
        "name": "LibreOffice Fresh",
        "pkg": "libreoffice-fresh",
        "source": "pacman",
        "category": "Productivity",
        "icon": "📑",
        "version": "24.8.0",
        "size": "160 MB",
        "desc": "Full office productivity suite including Writer, Calc spreadsheets, Impress presentations, and Draw.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux office suite"
    },
    {
        "name": "Obsidian Knowledge Base",
        "pkg": "md.obsidian.Obsidian",
        "source": "flatpak",
        "category": "Productivity",
        "icon": "💎",
        "version": "1.6.7",
        "size": "85 MB",
        "desc": "Second brain and Markdown note-taking app with bidirectional graph linking.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed Flathub container"
    },
    {
        "name": "Thunderbird Mail",
        "pkg": "thunderbird",
        "source": "pacman",
        "category": "Productivity",
        "icon": "✉️",
        "version": "128.1.0",
        "size": "70 MB",
        "desc": "Full-featured secure email, calendar, and address book client with PGP encryption.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Official Arch Linux email client"
    },
    {
        "name": "Bitwarden Vault",
        "pkg": "bitwarden",
        "source": "pacman",
        "category": "Productivity",
        "icon": "🛡️",
        "version": "2024.7.1",
        "size": "85 MB",
        "desc": "End-to-end encrypted password manager and 2FA authenticator for all devices.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux secure vault"
    },

    # Gaming & UACL
    {
        "name": "Steam & Proton",
        "pkg": "steam",
        "source": "pacman",
        "category": "Gaming & UACL",
        "icon": "🎮",
        "version": "1.0.0.79",
        "size": "65 MB",
        "desc": "The ultimate gaming platform with Proton DXVK/VKD3D compatibility for thousands of titles.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native client with Vulkan translation layers"
    },
    {
        "name": "Heroic Games Launcher",
        "pkg": "com.heroicgameslauncher.hgl",
        "source": "flatpak",
        "category": "Gaming & UACL",
        "icon": "⚔️",
        "version": "2.14.1",
        "size": "95 MB",
        "desc": "Native GUI launcher for Epic Games, GOG, and Amazon Prime with Proton wine prefix manager.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed Flathub gaming client"
    },
    {
        "name": "Lutris Gaming Platform",
        "pkg": "lutris",
        "source": "pacman",
        "category": "Gaming & UACL",
        "icon": "🕹️",
        "version": "0.5.17",
        "size": "25 MB",
        "desc": "Open gaming platform to install and manage Windows, Linux, emulator, and console games.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Linux gaming manager"
    },
    {
        "name": "RetroArch Multi-Emulator",
        "pkg": "retroarch",
        "source": "pacman",
        "category": "Gaming & UACL",
        "icon": "👾",
        "version": "1.19.1",
        "size": "40 MB",
        "desc": "Frontend for game engines and classic console emulators with low latency and shaders.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Native Vulkan/OpenGL emulator engine"
    },
    {
        "name": "Discord",
        "pkg": "com.discordapp.Discord",
        "source": "flatpak",
        "category": "Gaming & UACL",
        "icon": "💬",
        "version": "0.0.60",
        "size": "85 MB",
        "desc": "Voice, video, and text communication service for gaming, developers, and communities.",
        "compat": CompatibilityRating.NATIVE,
        "compat_desc": "Sandboxed Flathub container with PipeWire audio"
    },
    {
        "name": "Notepad++ (Win32)",
        "pkg": "npp.installer.exe",
        "source": "uacl",
        "category": "Gaming & UACL",
        "icon": "🪟",
        "version": "8.6.9",
        "size": "15 MB",
        "desc": "Classic lightweight Win32 source code editor running through Theonix UACL.",
        "compat": CompatibilityRating.UACL_COMPATIBLE,
        "compat_desc": "Windows binary managed seamlessly by Theonix UACL"
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
        dlg = AppInstallDialog(data, self.parent())
        dlg.exec()


class PackageInstallWorker(QThread):
    log_received = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, app_data: dict):
        super().__init__()
        self.app_data = app_data
        self.pkg = app_data.get("pkg", app_data["name"])
        self.source = app_data.get("source", "pacman")

    def run(self):
        if self.source == "pacman":
            # Use pkexec with database refresh (-Sy) to always fetch fresh mirror links
            cmd = ["pkexec", "pacman", "-Sy", "--needed", "--noconfirm", self.pkg]
        elif self.source == "flatpak":
            # User-level flatpak installs without requiring root permissions
            cmd = ["flatpak", "install", "-y", "--user", "flathub", self.pkg]
        elif self.source == "uacl":
            uacl_cache_dir = os.path.expanduser("~/.cache/theonix/uacl")
            os.makedirs(uacl_cache_dir, exist_ok=True)
            local_exe = os.path.join(uacl_cache_dir, self.pkg)

            if not os.path.exists(local_exe):
                self.log_received.emit(f"📥 Downloading Windows application package ({self.pkg})...\n")
                try:
                    import urllib.request
                    download_url = self.app_data.get(
                        "download_url", 
                        "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.9/npp.8.6.9.Installer.x64.exe"
                    )
                    urllib.request.urlretrieve(download_url, local_exe)
                    self.log_received.emit(f"✓ Package downloaded successfully to {local_exe}\n")
                except Exception as e:
                    self.finished.emit(False, f"Download failed: {e}")
                    return

            self.log_received.emit(f"🚀 Initializing Theonix UACL Proton/Wine container for {self.pkg}...\n")
            UACLService.launch(local_exe)
            self.finished.emit(True, "Launched with Theonix UACL.")
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
        self.worker = PackageInstallWorker(app_data)
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
        src = self.app_data.get("source", "pacman")
        if src == "pacman":
            bin_name = pkg.split(".")[0]
            subprocess.Popen([bin_name], stderr=subprocess.DEVNULL)
        elif src == "flatpak":
            subprocess.Popen(["flatpak", "run", pkg], stderr=subprocess.DEVNULL)
        elif src == "uacl":
            uacl_cache_dir = os.path.expanduser("~/.cache/theonix/uacl")
            local_exe = os.path.join(uacl_cache_dir, pkg)
            UACLService.launch(local_exe if os.path.exists(local_exe) else pkg)
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

        pkg = self.data.get("pkg", self.data["name"])
        src = self.data.get("source", "pacman")
        is_installed = self.data.get("installed") or PackageService.is_installed(pkg, src)

        compat_val = self.data.get("compat", CompatibilityRating.NATIVE)
        if compat_val == CompatibilityRating.NATIVE:
            badge = Badge("NATIVE", "green")
        elif compat_val == CompatibilityRating.UACL_COMPATIBLE:
            badge = Badge("UACL", "cyan")
        else:
            badge = Badge("CONFIG", "yellow")

        # Source engine badge
        if src in ["pacman", "arch"]:
            src_badge = Badge("📦 Arch (pacman)", "blue")
        elif src in ["flatpak", "flathub"]:
            src_badge = Badge("🌐 Flathub (Flatpak)", "purple")
        elif src == "uacl":
            src_badge = Badge("🪟 Windows (UACL)", "cyan")
        elif src == "aur":
            src_badge = Badge("⚡ AUR", "yellow")
        else:
            src_badge = Badge(src.upper(), "indigo")

        if is_installed:
            inst_badge = Badge("✓ INSTALLED", "green")
            h_title.addWidget(inst_badge)

        h_title.addWidget(src_badge)
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

        if is_installed:
            launch_btn = QPushButton("🚀 Launch")
            launch_btn.setProperty("class", "PrimaryBtn")
            launch_btn.setFixedWidth(100)
            launch_btn.clicked.connect(self._launch_app)
            layout.addWidget(launch_btn)
        else:
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

    def _launch_app(self):
        pkg = self.data.get("pkg", self.data["name"])
        src = self.data.get("source", "pacman")
        if src == "pacman":
            bin_name = pkg.split(".")[0]
            subprocess.Popen([bin_name], stderr=subprocess.DEVNULL)
        elif src == "flatpak":
            subprocess.Popen(["flatpak", "run", pkg], stderr=subprocess.DEVNULL)
        elif src == "uacl":
            uacl_cache_dir = os.path.expanduser("~/.cache/theonix/uacl")
            local_exe = os.path.join(uacl_cache_dir, pkg)
            UACLService.launch(local_exe if os.path.exists(local_exe) else pkg)


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

        mgr_btn = QPushButton("Installed Apps")
        mgr_btn.setProperty("class", "ActionBtn")
        mgr_btn.clicked.connect(self._open_installed_manager)

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

    def _open_installed_manager(self):
        btn = self.btn_group.button(6)
        if btn:
            btn.setChecked(True)
            self._on_category_changed(6)

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
            installed_apps = PackageService.get_installed_apps()
            hdr = QLabel(f"📥 Installed Applications ({len(installed_apps)} detected)")
            hdr.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
            self.cards_layout.addWidget(hdr)
            
            sub = QLabel("Native system binaries, sandboxed Flatpaks, and UACL Windows apps available on your device.")
            sub.setStyleSheet("color: #94A3B8; font-size: 13px; margin-bottom: 8px;")
            self.cards_layout.addWidget(sub)

            for app_data in installed_apps:
                card = AppCard(app_data, self)
                self.cards_layout.addWidget(card)

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

            filtered = [
                a for a in FEATURED_APPS 
                if cat_name.lower() in a.get("category", "").lower() or a.get("category", "").lower() in cat_name.lower()
            ]
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
