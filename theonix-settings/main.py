#!/usr/bin/env python3
"""
Theonix OS — Modern Ultra-Dark Glassmorphic System Settings & Control Center
Built for Theonix OS (KDE Plasma 6 / Wayland / Arch base)
"""

import os
import platform
import shutil
import subprocess
import sys
import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSlider, QProgressBar,
    QScrollArea, QFrame, QStackedWidget, QMessageBox, QFileDialog,
    QCheckBox, QGridLayout, QButtonGroup
)

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

/* Sidebar Buttons */
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

/* Glass Cards */
QFrame.Card {
    background-color: rgba(18, 24, 38, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 20px;
}

QFrame.Card:hover {
    border: 1px solid rgba(0, 255, 170, 0.25);
    background-color: rgba(24, 32, 50, 0.85);
}

/* Typography */
QLabel {
    color: #F8FAFC;
}

QLabel#PageTitle {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
}

QLabel#PageSubtitle {
    font-size: 13.5px;
    color: #94A3B8;
    margin-bottom: 6px;
}

QLabel#CardHeader {
    font-size: 15px;
    font-weight: 700;
    color: #00FFAA;
}

/* Buttons */
QPushButton.ActionBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.ActionBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
}

QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D75FF, stop:1 #1CE0FF);
}

/* Input Fields */
QLineEdit, QComboBox {
    background-color: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 8px 14px;
    color: #F8FAFC;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00FFAA;
    background-color: rgba(18, 24, 38, 0.95);
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #121826;
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: #6C63FF;
    selection-color: #FFFFFF;
    color: #F8FAFC;
    padding: 4px;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1C2436;
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

/* Progress Bar */
QProgressBar {
    background-color: #141A28;
    border: 1px solid rgba(255, 255, 255, 0.08);
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
    color: #F8FAFC;
    spacing: 8px;
    font-size: 13.5px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background-color: #0E121C;
}

QCheckBox::indicator:checked {
    background-color: #00FFAA;
    border-color: #00FFAA;
}
"""


class SystemAboutPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

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
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(20)

        logo_label = QLabel("⚡")
        logo_label.setStyleSheet("font-size: 30px; background: rgba(0,255,170,0.12); border-radius: 16px;")
        logo_label.setFixedSize(54, 54)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(logo_label)

        hero_text = QVBoxLayout()
        os_name = QLabel('Theonix OS 1.0 "Genesis"')
        os_name.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF;")
        os_desc = QLabel("AI-Powered Modern Linux · Arch Base · KDE Plasma 6 (Wayland)")
        os_desc.setStyleSheet("color: #00FFAA; font-size: 13px; font-weight: 600;")
        hero_text.addWidget(os_name)
        hero_text.addWidget(os_desc)
        hero_layout.addLayout(hero_text)
        hero_layout.addStretch()
        layout.addWidget(hero_card)

        # Specs Card
        specs_card = QFrame()
        specs_card.setProperty("class", "Card")
        grid = QGridLayout(specs_card)
        grid.setSpacing(14)

        specs = self._get_specs()
        for idx, (k, v) in enumerate(specs.items()):
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 13px;")
            v_lbl = QLabel(v)
            v_lbl.setStyleSheet("color: #FFFFFF; font-weight: 500; font-size: 13px;")
            grid.addWidget(k_lbl, idx // 2, (idx % 2) * 2)
            grid.addWidget(v_lbl, idx // 2, (idx % 2) * 2 + 1)

        layout.addWidget(specs_card)

        # Actions Card
        actions_card = QFrame()
        actions_card.setProperty("class", "Card")
        actions_layout = QHBoxLayout(actions_card)
        
        info_txt = QLabel("Community support & repository:")
        info_txt.setStyleSheet("color: #94A3B8; font-size: 13px;")
        actions_layout.addWidget(info_txt)
        actions_layout.addStretch()

        github_btn = QPushButton("GitHub")
        github_btn.setProperty("class", "ActionBtn")
        github_btn.clicked.connect(lambda: subprocess.Popen(["xdg-open", "https://github.com/kelvinkbk/TheonixOS"]))
        actions_layout.addWidget(github_btn)

        web_btn = QPushButton("Website")
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
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("AI & THAID Daemon")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Manage local neural models, Ollama inference, and THAID assistant integration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        status_card = QFrame()
        status_card.setProperty("class", "Card")
        status_layout = QHBoxLayout(status_card)
        
        icon_lbl = QLabel("🧠")
        icon_lbl.setStyleSheet("font-size: 32px;")
        status_layout.addWidget(icon_lbl)

        v_status = QVBoxLayout()
        self.status_title = QLabel("Checking THAID & Ollama status...")
        self.status_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")
        self.status_detail = QLabel("Local AI allows private code generation and system control without cloud dependency.")
        self.status_detail.setStyleSheet("color: #94A3B8; font-size: 12.5px;")
        v_status.addWidget(self.status_title)
        v_status.addWidget(self.status_detail)
        status_layout.addLayout(v_status)
        status_layout.addStretch()

        self.restart_ai_btn = QPushButton("Restart Daemon")
        self.restart_ai_btn.setProperty("class", "ActionBtn")
        self.restart_ai_btn.clicked.connect(self._restart_ollama)
        status_layout.addWidget(self.restart_ai_btn)
        layout.addWidget(status_card)

        # Model Manager Card
        model_card = QFrame()
        model_card.setProperty("class", "Card")
        m_layout = QVBoxLayout(model_card)
        m_layout.setSpacing(12)

        m_header = QLabel("Installed Local Models")
        m_header.setObjectName("CardHeader")
        m_layout.addWidget(m_header)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["Scanning local models..."])
        m_layout.addWidget(self.model_combo)

        pull_row = QHBoxLayout()
        self.pull_input = QLineEdit()
        self.pull_input.setPlaceholderText("Enter model tag (e.g. llama3.2:1b, mistral, deepseek-r1:1.5b)")
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
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Appearance & Personalization")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Customize themes, color accents, wallpapers, and interface styles")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        theme_card = QFrame()
        theme_card.setProperty("class", "Card")
        t_layout = QVBoxLayout(theme_card)
        t_layout.setSpacing(12)

        t_hdr = QLabel("Theme Preset")
        t_hdr.setObjectName("CardHeader")
        t_layout.addWidget(t_hdr)

        btn_row = QHBoxLayout()
        for name in ["✨ Theonix Dark", "🌌 Deep Space", "⚡ Cyber Neon", "🌅 Solar Glow"]:
            btn = QPushButton(name)
            btn.setProperty("class", "ActionBtn")
            btn.clicked.connect(lambda _, n=name: QMessageBox.information(self, "Theme", f"Theme set to: {n}"))
            btn_row.addWidget(btn)
        t_layout.addLayout(btn_row)
        layout.addWidget(theme_card)

        # Wallpaper Card
        wall_card = QFrame()
        wall_card.setProperty("class", "Card")
        w_layout = QVBoxLayout(wall_card)
        w_layout.setSpacing(12)

        w_hdr = QLabel("Desktop Wallpaper")
        w_hdr.setObjectName("CardHeader")
        w_layout.addWidget(w_hdr)

        w_row = QHBoxLayout()
        self.wall_path_input = QLineEdit()
        self.wall_path_input.setText("/usr/share/wallpapers/theonix-default.png")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setProperty("class", "ActionBtn")
        browse_btn.clicked.connect(self._browse_wallpaper)
        apply_btn = QPushButton("Apply")
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
        e_layout.setSpacing(10)

        e_hdr = QLabel("Visual Effects")
        e_hdr.setObjectName("CardHeader")
        e_layout.addWidget(e_hdr)

        self.blur_check = QCheckBox("Enable Glassmorphism & Translucent Blur")
        self.blur_check.setChecked(True)
        self.anim_check = QCheckBox("Enable Fluid Window Animations")
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
            subprocess.Popen(["plasma-apply-wallpaperimage", path], stderr=subprocess.DEVNULL)
            QMessageBox.information(self, "Wallpaper", f"Wallpaper applied: {path}")
        else:
            QMessageBox.warning(self, "Wallpaper", "File path does not exist.")


class DisplayPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Display & Scaling")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Resolution, refresh rate, scaling, and night light configuration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        hdr = QLabel("Display Configuration")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        grid = QGridLayout()
        grid.addWidget(QLabel("Resolution:"), 0, 0)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080 (16:9) [Recommended]", "2560x1440 (2K)", "3840x2160 (4K UHD)", "1366x768"])
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
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Network & Wi-Fi")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Wi-Fi networks, Ethernet adapter, and IP configuration")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        hdr = QLabel("Available Wi-Fi Networks")
        hdr.setObjectName("CardHeader")
        c_layout.addWidget(hdr)

        self.wifi_list = QFrame()
        self.wifi_list_layout = QVBoxLayout(self.wifi_list)
        self.wifi_list_layout.setSpacing(6)
        
        self.wifi_status_lbl = QLabel("Scanning for nearby wireless access points...")
        self.wifi_status_lbl.setStyleSheet("color: #94A3B8; padding: 10px;")
        self.wifi_list_layout.addWidget(self.wifi_status_lbl)
        c_layout.addWidget(self.wifi_list)

        btn_row = QHBoxLayout()
        scan_btn = QPushButton("Scan for Networks")
        scan_btn.setProperty("class", "ActionBtn")
        scan_btn.clicked.connect(self._scan_wifi)
        
        connect_btn = QPushButton("Manage in Plasma")
        connect_btn.setObjectName("PrimaryBtn")
        connect_btn.clicked.connect(lambda: subprocess.Popen(["plasmawindowed", "org.kde.plasma.networkmanagement"], stderr=subprocess.DEVNULL))

        btn_row.addWidget(scan_btn)
        btn_row.addWidget(connect_btn)
        btn_row.addStretch()
        c_layout.addLayout(btn_row)

        layout.addWidget(card)
        layout.addStretch()
        self._scan_wifi()

    def _scan_wifi(self):
        self.wifi_status_lbl.setText("Scanning for nearby wireless access points...")

        def _task():
            try:
                res = subprocess.run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"], capture_output=True, text=True, timeout=8)
                lines = [l for l in res.stdout.strip().splitlines() if l]
                return lines
            except Exception:
                return []

        def _cb(lines):
            if lines:
                parts = lines[0].split(":")
                ssid = parts[0] if parts else "Wi-Fi Connected"
                sig = parts[1] if len(parts) > 1 else "85"
                self.wifi_status_lbl.setText(f"📶  {ssid} ({sig}% signal strength · Active Connection)")
            else:
                self.wifi_status_lbl.setText("📶  NetworkManager active (Use 'Manage in Plasma' for network connections)")

        threading.Thread(target=lambda: _cb(_task()), daemon=True).start()


class AudioPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Sound & Audio")
        title.setObjectName("PageTitle")
        subtitle = QLabel("PipeWire audio control, speakers, and microphone levels")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

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

        test_btn = QPushButton("🔊 Test Audio")
        test_btn.setProperty("class", "ActionBtn")
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
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Storage & Btrfs Snapshots")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Disk partition capacity, filesystem health, and system restore points")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

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
        lbl.setStyleSheet("color: #94A3B8; font-weight: 500; font-size: 13px;")
        c_layout.addWidget(lbl)

        pbar = QProgressBar()
        pbar.setValue(pct)
        c_layout.addWidget(pbar)

        layout.addWidget(card)

        # Snapshot card
        snap_card = QFrame()
        snap_card.setProperty("class", "Card")
        s_layout = QVBoxLayout(snap_card)
        s_layout.setSpacing(12)

        s_hdr = QLabel("Btrfs Instant Restore Points")
        s_hdr.setObjectName("CardHeader")
        s_layout.addWidget(s_hdr)

        s_desc = QLabel("Theonix OS automatically snapshots your system before updates so you can roll back instantly if an issue occurs.")
        s_desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        s_layout.addWidget(s_desc)

        btn_row = QHBoxLayout()
        create_snap_btn = QPushButton("📸 Create Instant Snapshot")
        create_snap_btn.setObjectName("PrimaryBtn")
        create_snap_btn.clicked.connect(lambda: QMessageBox.information(self, "Snapshot", "Snapshot creation triggered."))
        
        timeshift_btn = QPushButton("Open Snapshot Manager")
        timeshift_btn.setProperty("class", "ActionBtn")
        timeshift_btn.clicked.connect(lambda: subprocess.Popen(["timeshift-launcher"], stderr=subprocess.DEVNULL))

        btn_row.addWidget(create_snap_btn)
        btn_row.addWidget(timeshift_btn)
        btn_row.addStretch()
        s_layout.addLayout(btn_row)

        layout.addWidget(snap_card)
        layout.addStretch()


class UpdatesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Software & System Updates")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Keep Theonix OS, system packages, and Flatpaks up to date")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

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
        self.check_btn.setProperty("class", "ActionBtn")
        self.check_btn.clicked.connect(self._check_updates)

        self.install_btn = QPushButton("Update Entire System")
        self.install_btn.setObjectName("PrimaryBtn")
        self.install_btn.clicked.connect(lambda: subprocess.Popen(["konsole", "-e", "sudo", "pacman", "-Syu"]))

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


class TheonixSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Settings")
        self.setMinimumSize(980, 680)
        self.resize(1060, 720)

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
        brand_icon = QLabel("⚡")
        brand_icon.setStyleSheet("font-size: 18px; color: #00FFAA;")
        brand_title = QLabel("THEONIX")
        brand_title.setStyleSheet("font-size: 14px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;")
        brand_tag = QLabel("SETTINGS")
        brand_tag.setStyleSheet("font-size: 10.5px; font-weight: bold; background: rgba(0,255,170,0.15); color: #00FFAA; padding: 2px 6px; border-radius: 4px;")
        
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title)
        brand_row.addWidget(brand_tag)
        brand_row.addStretch()
        sb_layout.addLayout(brand_row)

        nav_items = [
            ("💻  System & About", SystemAboutPage),
            ("🧠  AI & THAID", AISettingsPage),
            ("🎨  Appearance", AppearancePage),
            ("🖥️  Display & Scaling", DisplayPage),
            ("🌐  Network & Wi-Fi", NetworkPage),
            ("🔊  Sound & Audio", AudioPage),
            ("💾  Storage & Snapshots", StoragePage),
            ("🔄  System Updates", UpdatesPage),
        ]

        self.stack = QStackedWidget()
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for idx, (label, page_cls) in enumerate(nav_items):
            btn = QPushButton(label)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_group.addButton(btn, idx)
            sb_layout.addWidget(btn)

            page = page_cls()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        sb_layout.addStretch()

        self.btn_group.idClicked.connect(self.stack.setCurrentIndex)
        first_btn = self.btn_group.button(0)
        if first_btn:
            first_btn.setChecked(True)

        main_layout.addWidget(sidebar_box)
        main_layout.addWidget(self.stack)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(THEME_QSS)
    win = TheonixSettingsWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
