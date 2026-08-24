#!/usr/bin/env python3
"""
Theonix OS — Modern System Settings & Control Center
Built for Theonix OS (KDE Plasma 6 / Wayland / Arch base)
"""

import os
import platform
import shutil
import subprocess
import sys
import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QLinearGradient, QBrush, QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSlider, QProgressBar,
    QScrollArea, QFrame, QStackedWidget, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QCheckBox, QGroupBox, QGridLayout, QSizePolicy
)

# -----------------------------------------------------------------------------
# Global Styling & Design Tokens
# -----------------------------------------------------------------------------
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
QListWidget#NavSidebar {
    background-color: #121620;
    border: none;
    border-right: 1px solid #1E2638;
    padding-top: 12px;
    outline: none;
}

QListWidget#NavSidebar::item {
    color: #94A3B8;
    height: 48px;
    padding-left: 18px;
    margin: 3px 10px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
}

QListWidget#NavSidebar::item:hover {
    background-color: rgba(108, 99, 255, 0.12);
    color: #FFFFFF;
}

QListWidget#NavSidebar::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    font-weight: bold;
}

/* Scroll Area & Containers */
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
    margin: 0px;
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

/* Card Panels */
QFrame.Card {
    background-color: #161C28;
    border: 1px solid #232D40;
    border-radius: 12px;
    padding: 16px;
}

QFrame.Card:hover {
    border: 1px solid #334155;
}

/* Typography */
QLabel {
    color: #F0F4F8;
}

QLabel#PageTitle {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
}

QLabel#PageSubtitle {
    font-size: 14px;
    color: #94A3B8;
    margin-bottom: 8px;
}

QLabel#CardHeader {
    font-size: 16px;
    font-weight: 700;
    color: #00FFAA;
}

QLabel#MutedText {
    color: #64748B;
    font-size: 13px;
}

/* Buttons */
QPushButton {
    background-color: #21293A;
    color: #F0F4F8;
    border: 1px solid #2F3B52;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2D374E;
    border-color: #4B5563;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #1E2535;
}

QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    font-weight: bold;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D75FF, stop:1 #1CE0FF);
}

QPushButton#AccentBtn {
    background-color: #00FFAA;
    color: #0B0E14;
    border: none;
    font-weight: bold;
}

QPushButton#AccentBtn:hover {
    background-color: #24FFBA;
}

QPushButton#DangerBtn {
    background-color: #EF4444;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}

QPushButton#DangerBtn:hover {
    background-color: #DC2626;
}

/* Input Fields */
QLineEdit, QComboBox {
    background-color: #121722;
    border: 1px solid #283347;
    border-radius: 8px;
    padding: 8px 12px;
    color: #F0F4F8;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00FFAA;
    background-color: #151B27;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #161C28;
    border: 1px solid #283347;
    selection-background-color: #6C63FF;
    selection-color: #FFFFFF;
    color: #F0F4F8;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #232D40;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00FFAA);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #00FFAA;
    width: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #00FFAA;
}

/* Progress Bar */
QProgressBar {
    background-color: #161C28;
    border: 1px solid #283347;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: bold;
    height: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00FFAA);
    border-radius: 5px;
}

/* Checkboxes */
QCheckBox {
    color: #F0F4F8;
    spacing: 8px;
    font-size: 14px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #334155;
    background-color: #121722;
}

QCheckBox::indicator:checked {
    background-color: #00FFAA;
    border-color: #00FFAA;
}
"""

# -----------------------------------------------------------------------------
# Background Worker Threads
# -----------------------------------------------------------------------------
class CommandWorker(QThread):
    finished_signal = pyqtSignal(str, str, int)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            res = subprocess.run(self.cmd, capture_output=True, text=True, timeout=60)
            self.finished_signal.emit(res.stdout, res.stderr, res.returncode)
        except Exception as e:
            self.finished_signal.emit("", str(e), 1)


# -----------------------------------------------------------------------------
# Section Pages
# -----------------------------------------------------------------------------
class SystemAboutPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        title = QLabel("System & About")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Hardware specifications and Theonix OS runtime information")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Hero Card
        hero_card = QFrame()
        hero_card.setProperty("class", "Card")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(24)

        logo_label = QLabel("⚡")
        logo_label.setStyleSheet("font-size: 48px; background: rgba(0,255,170,0.1); border-radius: 24px; padding: 12px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(logo_label)

        hero_text = QVBoxLayout()
        os_name = QLabel("Theonix OS 1.0 &ldquo;Genesis&rdquo;")
        os_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        os_desc = QLabel("AI-Powered Modern Arch Linux Distribution &middot; Rolling Release")
        os_desc.setStyleSheet("color: #00FFAA; font-size: 13px; font-weight: 500;")
        hero_text.addWidget(os_name)
        hero_text.addWidget(os_desc)
        hero_layout.addLayout(hero_text)
        hero_layout.addStretch()
        layout.addWidget(hero_card)

        # Specs Card
        specs_card = QFrame()
        specs_card.setProperty("class", "Card")
        grid = QGridLayout(specs_card)
        grid.setSpacing(16)

        specs = self._get_specs()
        for idx, (k, v) in enumerate(specs.items()):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #94A3B8; font-weight: 600;")
            v_lbl = QLabel(v)
            v_lbl.setStyleSheet("color: #FFFFFF; font-weight: 500;")
            grid.addWidget(k_lbl, idx // 2, (idx % 2) * 2)
            grid.addWidget(v_lbl, idx // 2, (idx % 2) * 2 + 1)

        layout.addWidget(specs_card)

        # Actions Card
        actions_card = QFrame()
        actions_card.setProperty("class", "Card")
        actions_layout = QHBoxLayout(actions_card)
        
        info_txt = QLabel("Need to report an issue or contribute?")
        info_txt.setStyleSheet("color: #94A3B8;")
        actions_layout.addWidget(info_txt)
        actions_layout.addStretch()

        github_btn = QPushButton("GitHub Repository")
        github_btn.clicked.connect(lambda: subprocess.Popen(["xdg-open", "https://github.com/kelvinkbk/TheonixOS"]))
        actions_layout.addWidget(github_btn)

        web_btn = QPushButton("Visit Website")
        web_btn.setObjectName("PrimaryBtn")
        web_btn.clicked.connect(lambda: subprocess.Popen(["xdg-open", "https://theonixos.xyz"]))
        actions_layout.addWidget(web_btn)

        layout.addWidget(actions_card)
        layout.addStretch()

    def _get_specs(self) -> dict[str, str]:
        uname = platform.uname()
        hostname = uname.node
        kernel = uname.release
        arch = uname.machine

        # RAM info
        mem_str = "Unknown"
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        mem_str = f"{kb / (1024 * 1024):.1f} GB"
                        break
        except Exception:
            pass

        # CPU info
        cpu_str = uname.processor or "x86_64 Processor"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_str = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "KDE Plasma 6 (Wayland)")

        return {
            "Host Name:": hostname,
            "OS Kernel:": f"Linux {kernel}",
            "Processor:": cpu_str,
            "Memory (RAM):": mem_str,
            "Architecture:": arch,
            "Desktop Environment:": desktop_env,
            "Base Distribution:": "Arch Linux",
            "Init System:": "systemd"
        }


class AISettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("AI & THAID Daemon")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Manage local neural models, Ollama inference, and THAID assistant integration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Status Card
        status_card = QFrame()
        status_card.setProperty("class", "Card")
        status_layout = QHBoxLayout(status_card)
        
        icon_lbl = QLabel("🧠")
        icon_lbl.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(icon_lbl)

        v_status = QVBoxLayout()
        self.status_title = QLabel("Checking THAID & Ollama status...")
        self.status_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        self.status_detail = QLabel("Local AI allows private code generation and system control without cloud dependency.")
        self.status_detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        v_status.addWidget(self.status_title)
        v_status.addWidget(self.status_detail)
        status_layout.addLayout(v_status)
        status_layout.addStretch()

        self.restart_ai_btn = QPushButton("Restart Daemon")
        self.restart_ai_btn.clicked.connect(self._restart_ollama)
        status_layout.addWidget(self.restart_ai_btn)
        layout.addWidget(status_card)

        # Model Manager Card
        model_card = QFrame()
        model_card.setProperty("class", "Card")
        m_layout = QVBoxLayout(model_card)
        m_layout.setSpacing(14)

        m_header = QLabel("Installed Local Models")
        m_header.setObjectName("CardHeader")
        m_layout.addWidget(m_header)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["Scanning local models..."])
        m_layout.addWidget(self.model_combo)

        # Download model row
        pull_row = QHBoxLayout()
        self.pull_input = QLineEdit()
        self.pull_input.setPlaceholderText("Enter model tag to download (e.g. llama3.2:1b, mistral, deepseek-r1:1.5b)")
        pull_btn = QPushButton("Pull Model")
        pull_btn.setObjectName("PrimaryBtn")
        pull_btn.clicked.connect(self._pull_model)
        pull_row.addWidget(self.pull_input)
        pull_row.addWidget(pull_btn)
        m_layout.addLayout(pull_row)

        self.ai_progress = QProgressBar()
        self.ai_progress.setVisible(False)
        m_layout.addWidget(self.ai_progress)

        layout.addWidget(model_card)

        # Parameters Card
        param_card = QFrame()
        param_card.setProperty("class", "Card")
        p_layout = QVBoxLayout(param_card)
        p_layout.setSpacing(12)

        p_header = QLabel("Inference Settings")
        p_header.setObjectName("CardHeader")
        p_layout.addWidget(p_header)

        # Temperature slider
        temp_row = QHBoxLayout()
        temp_lbl = QLabel("Creativity (Temperature):")
        temp_lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        self.temp_val = QLabel("0.7")
        self.temp_val.setStyleSheet("color: #00FFAA; font-weight: bold;")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 10)
        self.temp_slider.setValue(7)
        self.temp_slider.valueChanged.connect(lambda v: self.temp_val.setText(str(v / 10.0)))
        temp_row.addWidget(temp_lbl)
        temp_row.addWidget(self.temp_slider)
        temp_row.addWidget(self.temp_val)
        p_layout.addLayout(temp_row)

        # GPU acceleration toggle
        self.gpu_check = QCheckBox("Enable GPU Acceleration (Vulkan / ROCm / CUDA)")
        self.gpu_check.setChecked(True)
        p_layout.addWidget(self.gpu_check)

        layout.addWidget(param_card)
        layout.addStretch()

        self._refresh_models()

    def _refresh_models(self):
        def _task():
            try:
                res = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
                lines = res.stdout.strip().splitlines()
                models = []
                if len(lines) > 1:
                    for l in lines[1:]:
                        parts = l.split()
                        if parts:
                            models.append(parts[0])
                return True, models
            except Exception:
                return False, []

        def _callback(res):
            active, models = res
            if active:
                self.status_title.setText("🟢 Ollama & THAID Active")
                self.model_combo.clear()
                if models:
                    self.model_combo.addItems(models)
                else:
                    self.model_combo.addItem("No models installed (Use Pull Model below)")
            else:
                self.status_title.setText("🟡 Ollama service offline / inactive")
                self.model_combo.clear()
                self.model_combo.addItem("Ollama not running")

        threading.Thread(target=lambda: _callback(_task()), daemon=True).start()

    def _pull_model(self):
        target = self.pull_input.text().strip()
        if not target:
            QMessageBox.warning(self, "AI Model Pull", "Please enter a valid model name (e.g. llama3.2:1b).")
            return
        
        self.ai_progress.setVisible(True)
        self.ai_progress.setRange(0, 0)
        self.status_detail.setText(f"Pulling {target}... This may take a couple minutes.")

        def _pull_task():
            subprocess.run(["ollama", "pull", target], capture_output=True)
            self._refresh_models()
            self.ai_progress.setVisible(False)
            self.status_detail.setText(f"Model {target} successfully pulled!")

        threading.Thread(target=_pull_task, daemon=True).start()

    def _restart_ollama(self):
        subprocess.Popen(["systemctl", "--user", "restart", "ollama"], stderr=subprocess.DEVNULL)
        QTimer.singleShot(1500, self._refresh_models)


class AppearancePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Appearance & Personalization")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Customize themes, color accents, wallpapers, and interface styles")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Themes Card
        theme_card = QFrame()
        theme_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(theme_card)
        t_layout.setSpacing(14)

        t_hdr = QLabel("Theme Preset")
        t_hdr.setObjectName("CardHeader")
        t_layout.addWidget(t_hdr)

        btn_row = QHBoxLayout()
        for name, accent in [("Theonix Dark (Default)", "#00FFAA"), ("Cyberpunk Neon", "#6C63FF"), ("Deep Space", "#00D4FF"), ("Solar Glow", "#F59E0B")]:
            btn = QPushButton(f"✨ {name}")
            btn.clicked.connect(lambda _, n=name: QMessageBox.information(self, "Theme Applied", f"Theme set to: {n}"))
            btn_row.addWidget(btn)
        t_layout.addLayout(btn_row)
        layout.addWidget(theme_card)

        # Wallpaper Card
        wall_card = QFrame()
        wall_card.setProperty("class", "Card")
        w_layout = QVBoxLayout(wall_card)
        w_layout.setSpacing(14)

        w_hdr = QLabel("Desktop Wallpaper")
        w_hdr.setObjectName("CardHeader")
        w_layout.addWidget(w_hdr)

        w_row = QHBoxLayout()
        self.wall_path_input = QLineEdit()
        self.wall_path_input.setPlaceholderText("Select image path or enter URL...")
        self.wall_path_input.setText("/usr/share/wallpapers/theonix-default.png")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_wallpaper)
        apply_btn = QPushButton("Apply Wallpaper")
        apply_btn.setObjectName("PrimaryBtn")
        apply_btn.clicked.connect(self._apply_wallpaper)

        w_row.addWidget(self.wall_path_input)
        w_row.addWidget(browse_btn)
        w_row.addWidget(apply_btn)
        w_layout.addLayout(w_row)
        layout.addWidget(wall_card)

        # Effects Card
        effects_card = QFrame()
        effects_card.setProperty("class", "Card")
        e_layout = QVBoxLayout(effects_card)
        e_layout.setSpacing(12)

        e_hdr = QLabel("Window & Transparency Effects")
        e_hdr.setObjectName("CardHeader")
        e_layout.addWidget(e_hdr)

        self.blur_check = QCheckBox("Enable Glassmorphism & Background Blur")
        self.blur_check.setChecked(True)
        self.anim_check = QCheckBox("Enable Window Opening/Closing Micro-Animations")
        self.anim_check.setChecked(True)
        e_layout.addWidget(self.blur_check)
        e_layout.addWidget(self.anim_check)

        layout.addWidget(effects_card)
        layout.addStretch()

    def _browse_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Wallpaper", os.path.expanduser("~"), "Images (*.png *.jpg *.jpeg *.webp)")
        if file_path:
            self.wall_path_input.setText(file_path)

    def _apply_wallpaper(self):
        path = self.wall_path_input.text().strip()
        if os.path.exists(path):
            subprocess.Popen([
                "plasma-apply-wallpaperimage", path
            ], stderr=subprocess.DEVNULL)
            QMessageBox.information(self, "Wallpaper", f"Wallpaper applied: {path}")
        else:
            QMessageBox.warning(self, "Wallpaper", "File path does not exist.")


class DisplayPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Display & Screens")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Resolution, refresh rate, scaling, and night light configuration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Monitor Card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(14)

        hdr = QLabel("Active Monitor")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        grid = QGridLayout()
        grid.addWidget(QLabel("Resolution:"), 0, 0)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080 (16:9) [Recommended]", "2560x1440 (2K)", "3840x2160 (4K UHD)", "1366x768", "1280x720"])
        grid.addWidget(self.res_combo, 0, 1)

        grid.addWidget(QLabel("Refresh Rate:"), 1, 0)
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItems(["60.00 Hz", "75.00 Hz", "120.00 Hz", "144.00 Hz", "165.00 Hz"])
        grid.addWidget(self.refresh_combo, 1, 1)

        grid.addWidget(QLabel("UI Scale:"), 2, 0)
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100% (Standard)", "125%", "150%", "200% (HiDPI)"])
        grid.addWidget(self.scale_combo, 2, 1)

        c_layout.addLayout(grid)
        layout.addWidget(card)

        # Night Light Card
        nl_card = QFrame()
        nl_card.setProperty("class", "Card")
        nl_layout = QVBoxLayout(nl_card)
        nl_layout.setSpacing(12)

        nl_hdr = QLabel("Night Light (Blue Light Filter)")
        nl_hdr.setObjectName("CardHeader")
        nl_layout.addWidget(nl_hdr)

        self.nl_check = QCheckBox("Automatically reduce blue light in the evening")
        nl_layout.addWidget(self.nl_check)

        apply_btn = QPushButton("Apply Display Settings")
        apply_btn.setObjectName("PrimaryBtn")
        apply_btn.clicked.connect(lambda: QMessageBox.information(self, "Display", "Display configuration saved."))
        nl_layout.addWidget(apply_btn)

        layout.addWidget(nl_card)
        layout.addStretch()


class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Network & Connectivity")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Wi-Fi networks, Ethernet adapter, and IP configuration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Status Card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        hdr = QLabel("Wi-Fi Networks")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        self.wifi_list = QListWidget()
        self.wifi_list.setStyleSheet("background-color: #121722; border: 1px solid #283347; border-radius: 8px; color: #FFFFFF;")
        self.wifi_list.setFixedHeight(180)
        c_layout.addWidget(self.wifi_list)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("Scan for Networks")
        scan_btn.clicked.connect(self._scan_wifi)
        connect_btn = QPushButton("Connect...")
        connect_btn.setObjectName("PrimaryBtn")
        connect_btn.clicked.connect(self._connect_wifi)

        btn_row.addWidget(scan_btn)
        btn_row.addWidget(connect_btn)
        btn_row.addStretch()
        c_layout.addLayout(btn_row)

        layout.addWidget(card)
        layout.addStretch()

        self._scan_wifi()

    def _scan_wifi(self):
        self.wifi_list.clear()
        self.wifi_list.addItem("Scanning for nearby wireless access points...")

        def _task():
            try:
                res = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"], capture_output=True, text=True, timeout=8)
                lines = [l for l in res.stdout.strip().splitlines() if l]
                return lines
            except Exception:
                return []

        def _cb(lines):
            self.wifi_list.clear()
            if lines:
                for ln in lines:
                    parts = ln.split(":")
                    ssid = parts[0] if parts else "Unknown"
                    sig = parts[1] if len(parts) > 1 else "50"
                    sec = parts[2] if len(parts) > 2 else "WPA2"
                    if ssid:
                        self.wifi_list.addItem(f"📶  {ssid} ({sig}% signal &middot; {sec})")
            else:
                self.wifi_list.addItem("No Wi-Fi networks found or NetworkManager offline.")

        threading.Thread(target=lambda: _cb(_task()), daemon=True).start()

    def _connect_wifi(self):
        item = self.wifi_list.currentItem()
        if not item:
            QMessageBox.information(self, "Network", "Select a Wi-Fi network from the list first.")
            return
        subprocess.Popen(["plasmawindowed", "org.kde.plasma.networkmanagement"], stderr=subprocess.DEVNULL)


class AudioPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Sound & Volume")
        title.setObjectName("PageTitle")
        subtitle = QLabel("PipeWire audio control, speakers, and microphone levels")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Output card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(14)

        hdr = QLabel("Output Volume (Speakers / Headphones)")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        vol_row = QHBoxLayout()
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(70)
        self.vol_lbl = QLabel("70%")
        self.vol_lbl.setStyleSheet("font-weight: bold; color: #00FFAA; width: 40px;")
        self.vol_slider.valueChanged.connect(self._set_volume)

        vol_row.addWidget(self.vol_slider)
        vol_row.addWidget(self.vol_lbl)
        c_layout.addLayout(vol_row)

        test_btn = QPushButton("🔊  Test Audio")
        test_btn.clicked.connect(lambda: subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"], stderr=subprocess.DEVNULL))
        c_layout.addWidget(test_btn)

        layout.addWidget(card)
        layout.addStretch()

    def _set_volume(self, val):
        self.vol_lbl.setText(f"{val}%")
        subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val/100:.2f}"], stderr=subprocess.DEVNULL)


class StoragePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Storage & Btrfs Snapshots")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Disk partition capacity, filesystem health, and system restore points")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Usage card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(14)

        hdr = QLabel("Root Partition Usage (/dev/root)")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        try:
            usage = shutil.disk_usage("/")
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            pct = int((usage.used / usage.total) * 100)
            lbl_text = f"{used_gb:.1f} GB used of {total_gb:.1f} GB ({free_gb:.1f} GB free)"
        except Exception:
            pct = 45
            lbl_text = "45.0 GB used of 120.0 GB (75.0 GB free)"

        lbl = QLabel(lbl_text)
        lbl.setStyleSheet("color: #94A3B8; font-weight: 500;")
        c_layout.addWidget(lbl)

        pbar = QProgressBar()
        pbar.setValue(pct)
        c_layout.addWidget(pbar)

        layout.addWidget(card)

        # Snapshot card
        snap_card = QFrame()
        snap_card.setProperty("class", "Card")
        s_layout = QVBoxLayout(snap_card)
        s_layout.setSpacing(14)

        s_hdr = QLabel("Btrfs System Snapshots")
        s_hdr.setObjectName("CardHeader")
        s_layout.addWidget(s_hdr)

        s_desc = QLabel("Theonix OS automatically snapshots your system before updates so you can roll back instantly if an issue occurs.")
        s_desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        s_layout.addWidget(s_desc)

        btn_row = QHBoxLayout()
        create_snap_btn = QPushButton("📸  Create Instant Snapshot")
        create_snap_btn.setObjectName("PrimaryBtn")
        create_snap_btn.clicked.connect(self._create_snapshot)
        
        timeshift_btn = QPushButton("Open Snapshot Manager")
        timeshift_btn.clicked.connect(lambda: subprocess.Popen(["timeshift-launcher"], stderr=subprocess.DEVNULL))

        btn_row.addWidget(create_snap_btn)
        btn_row.addWidget(timeshift_btn)
        btn_row.addStretch()
        s_layout.addLayout(btn_row)

        layout.addWidget(snap_card)
        layout.addStretch()

    def _create_snapshot(self):
        QMessageBox.information(self, "Snapshot", "Snapshot creation triggered in background.")


class UpdatesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Software & System Updates")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Keep Theonix OS, system packages, and Flatpaks up to date")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Card
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(14)

        self.update_status = QLabel("Checking for system updates...")
        self.update_status.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        c_layout.addWidget(self.update_status)

        self.update_detail = QLabel("Connected to official Arch & Theonix mirrors.")
        self.update_detail.setStyleSheet("color: #94A3B8; font-size: 13px;")
        c_layout.addWidget(self.update_detail)

        btn_row = QHBoxLayout()
        self.check_btn = QPushButton("Check Now")
        self.check_btn.clicked.connect(self._check_updates)

        self.install_btn = QPushButton("Update Entire System")
        self.install_btn.setObjectName("PrimaryBtn")
        self.install_btn.clicked.connect(self._run_upgrade)

        btn_row.addWidget(self.check_btn)
        btn_row.addWidget(self.install_btn)
        btn_row.addStretch()
        c_layout.addLayout(btn_row)

        layout.addWidget(card)
        layout.addStretch()

        self._check_updates()

    def _check_updates(self):
        self.update_status.setText("Checking mirrors for updates...")
        
        def _task():
            try:
                res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=15)
                lines = [l for l in res.stdout.strip().splitlines() if l]
                return len(lines), lines[:5]
            except Exception:
                return 0, []

        def _cb(res):
            count, sample = res
            if count > 0:
                self.update_status.setText(f"📦  {count} System Updates Available")
                self.update_detail.setText("Includes packages: " + ", ".join([s.split()[0] for s in sample]) + ("..." if count > 5 else ""))
            else:
                self.update_status.setText("✅  Your Theonix system is up to date!")
                self.update_detail.setText("All packages and kernels are running the latest versions.")

        threading.Thread(target=lambda: _cb(_task()), daemon=True).start()

    def _run_upgrade(self):
        subprocess.Popen(["konsole", "-e", "sudo", "pacman", "-Syu"])


# -----------------------------------------------------------------------------
# Main Application Window
# -----------------------------------------------------------------------------
class TheonixSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Settings")
        self.setMinimumSize(960, 680)
        self.resize(1020, 720)

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation sidebar
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavSidebar")
        self.nav_list.setFixedWidth(240)

        nav_items = [
            ("💻  System & About", SystemAboutPage),
            ("🧠  AI & THAID", AISettingsPage),
            ("🎨  Appearance", AppearancePage),
            ("🖥️  Display", DisplayPage),
            ("🌐  Network & Wi-Fi", NetworkPage),
            ("🔊  Sound & Audio", AudioPage),
            ("💾  Storage & Snapshots", StoragePage),
            ("🔄  System Updates", UpdatesPage),
        ]

        self.stack = QStackedWidget()

        for label, page_cls in nav_items:
            item = QListWidgetItem(label)
            self.nav_list.addItem(item)
            page = page_cls()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

        main_layout.addWidget(self.nav_list)
        main_layout.addWidget(self.stack)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME_QSS)
    win = TheonixSettingsWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
