#!/usr/bin/env python3
"""
Theonix OS — Quick Settings & Taskbar Control Center (org.theonix.ControlCenter)
Pixel-perfect implementation of the refined Theonix Quick Settings prototype:
- Panel: linear-gradient(145deg, rgba(25,30,40,.98), rgba(14,18,25,.99)), 24px radius
- 2-Column Grid of 6 interactive tiles (Wi-Fi, Bluetooth, Airplane, Night Light, Battery Saver, Focus)
- Sliders: Brightness & Volume with dynamic percentage values and #7b61ff accent
- Footer: THAID Ready status with glowing teal dot + Settings & Lock action buttons
- Taskbar System Tray icon & D-Bus integration
"""

import sys
import os
import glob
import json
import shutil
import subprocess
from typing import Dict, Any

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QGraphicsDropShadowEffect, QGridLayout,
    QFrame, QDialog, QScrollArea, QLineEdit, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon, QPixmap, QPainter, QBrush, QPen
from PyQt6.QtDBus import QDBusConnection


# =============================================================================
# HARDWARE / SYSTEM TELEMETRY HELPERS
# =============================================================================

def get_battery_info() -> Dict[str, Any]:
    try:
        bats = glob.glob("/sys/class/power_supply/BAT*")
        if bats:
            bat_dir = bats[0]
            with open(os.path.join(bat_dir, "capacity")) as f:
                cap = int(f.read().strip())
            status = "Discharging"
            if os.path.exists(os.path.join(bat_dir, "status")):
                with open(os.path.join(bat_dir, "status")) as f:
                    status = f.read().strip()
            return {"capacity": cap, "status": status, "available": True}
    except Exception:
        pass
    return {"capacity": 78, "status": "Discharging", "available": False}


def get_wifi_status() -> Dict[str, Any]:
    res = {"enabled": True, "ssid": "Theonix_5G"}
    try:
        r = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=1)
        res["enabled"] = "enabled" in r.stdout.lower()

        if res["enabled"]:
            r2 = subprocess.run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], capture_output=True, text=True, timeout=1)
            for line in r2.stdout.splitlines():
                if line.startswith("yes:"):
                    res["ssid"] = line.split(":", 1)[1]
                    break
    except Exception:
        pass
    return res


def toggle_wifi(enable: bool) -> bool:
    try:
        arg = "on" if enable else "off"
        subprocess.run(["nmcli", "radio", "wifi", arg], timeout=2)
        return True
    except Exception:
        return False


def get_bluetooth_status() -> bool:
    try:
        if shutil.which("bluetoothctl"):
            r = subprocess.run(["bluetoothctl", "show"], capture_output=True, text=True, timeout=1)
            return "Powered: yes" in r.stdout
    except Exception:
        pass
    return True


def toggle_bluetooth(enable: bool) -> bool:
    try:
        if shutil.which("bluetoothctl"):
            arg = "power on" if enable else "power off"
            subprocess.run(["bluetoothctl", arg], timeout=2)
            return True
    except Exception:
        pass
    return False


def get_audio_volume() -> int:
    try:
        r = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=1)
        for part in r.stdout.split():
            if "%" in part:
                return int(part.replace("%", ""))
    except Exception:
        pass
    return 48


def set_audio_volume(vol: int):
    try:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{vol}%"], timeout=1)
    except Exception:
        pass


def get_screen_brightness() -> int:
    try:
        backlights = glob.glob("/sys/class/backlight/*")
        if backlights:
            b_dir = backlights[0]
            with open(os.path.join(b_dir, "brightness")) as f:
                curr = int(f.read().strip())
            with open(os.path.join(b_dir, "max_brightness")) as f:
                mx = int(f.read().strip())
            return max(5, int((curr / mx) * 100))
    except Exception:
        pass
    return 72


def set_screen_brightness(pct: int):
    try:
        if shutil.which("brightnessctl"):
            subprocess.run(["brightnessctl", "set", f"{pct}%"], timeout=1)
    except Exception:
        pass


# =============================================================================
# TRAY ICON GENERATOR
# =============================================================================

def create_tray_icon() -> QIcon:
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QBrush(QColor(32, 38, 49, 240)))
    painter.setPen(QPen(QColor(123, 97, 255, 200), 1.5))
    painter.drawRoundedRect(2, 2, 28, 28, 8, 8)

    painter.setBrush(QBrush(QColor(123, 97, 255)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(12, 12, 8, 8)

    painter.setPen(QPen(QColor(18, 216, 197, 200), 1.5))
    painter.drawEllipse(8, 8, 16, 16)

    painter.end()
    return QIcon(pix)


# =============================================================================
# PROTOTYPE QUICK TILE (2-COLUMN GRID)
# =============================================================================

class QuickTile(QFrame):
    toggled = pyqtSignal(bool)

    def __init__(self, icon_str: str, label_str: str, state_str: str, active: bool = False, has_arrow: bool = False, parent=None):
        super().__init__(parent)
        self.active = active
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(76)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Main Row
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(35, 35)
        i_lay = QVBoxLayout(self.icon_box)
        i_lay.setContentsMargins(0, 0, 0, 0)
        self.icon_lbl = QLabel(icon_str)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setFont(QFont("Inter", 14))
        i_lay.addWidget(self.icon_lbl)
        layout.addWidget(self.icon_box)

        # Label & State
        t_lay = QVBoxLayout()
        t_lay.setSpacing(2)
        self.label_lbl = QLabel(label_str)
        self.label_lbl.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.label_lbl.setStyleSheet("color: #f4f7fb;")

        self.state_lbl = QLabel(state_str)
        self.state_lbl.setFont(QFont("Inter", 10))
        self.state_lbl.setStyleSheet("color: #9ca7b7;")

        t_lay.addWidget(self.label_lbl)
        t_lay.addWidget(self.state_lbl)
        layout.addLayout(t_lay)
        layout.addStretch()

        if has_arrow:
            arrow = QLabel("›")
            arrow.setFont(QFont("Inter", 14, QFont.Weight.Bold))
            arrow.setStyleSheet("color: #9ca7b7;")
            layout.addWidget(arrow)

        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.active = not self.active
            self._update_style()
            self.toggled.emit(self.active)
        super().mousePressEvent(event)

    def set_state_text(self, text: str):
        self.state_lbl.setText(text)

    def set_active(self, active: bool):
        self.active = active
        self._update_style()

    def _update_style(self):
        if self.active:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(123,97,255,0.30), stop:1 rgba(18,216,197,0.08));
                    border: 1px solid #5c4fbd;
                    border-radius: 16px;
                }
                QLabel { background: transparent; }
            """)
            self.icon_box.setStyleSheet("background: rgba(123,97,255,0.34); border-radius: 11px;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background: #202631;
                    border: 1px solid #333c49;
                    border-radius: 16px;
                }
                QFrame:hover {
                    background: #29313d;
                    border-color: #434f60;
                }
                QLabel { background: transparent; }
            """)
            self.icon_box.setStyleSheet("background: #2b333f; border-radius: 11px;")


# =============================================================================
# THAID INTERACTIVE PROMPT DIALOG
# =============================================================================

class ThaidPromptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("THAID OS Assistant")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: #171c24;
                border: 1px solid #5c4fbd;
                border-radius: 20px;
            }
            QLabel { color: #f4f7fb; font-family: 'Inter'; }
        """)

        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 14, 16, 14)
        c_lay.setSpacing(10)

        h_row = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(1)
        t_title = QLabel("THAID OS Assistant")
        t_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        t_sub = QLabel("Local AI • Qwen 3.5 4B / Llama 3 8B")
        t_sub.setFont(QFont("Inter", 9))
        t_sub.setStyleSheet("color: #7b61ff;")
        t_box.addWidget(t_title)
        t_box.addWidget(t_sub)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("background: transparent; color: #9ca7b7; border: none; font-size: 13px; font-weight: bold;")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.close)

        h_row.addLayout(t_box)
        h_row.addStretch()
        h_row.addWidget(close_btn)
        c_lay.addLayout(h_row)

        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setStyleSheet("background: rgba(15, 18, 23, 0.6); border: 1px solid #333c49; border-radius: 12px;")
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(8)
        self.chat_area.setWidget(self.chat_container)

        self._add_message("bot", "Good afternoon! What would you like me to do?")
        c_lay.addWidget(self.chat_area)

        in_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: #202631;
                border: 1px solid #333c49;
                border-radius: 10px;
                padding: 8px 12px;
                color: #f4f7fb;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #7b61ff; }
        """)
        self.input_field.returnPressed.connect(self._send_message)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background: #7b61ff;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #8e77ff; }
        """)
        send_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        send_btn.clicked.connect(self._send_message)

        in_row.addWidget(self.input_field)
        in_row.addWidget(send_btn)
        c_lay.addLayout(in_row)

        layout.addWidget(card)

    def _add_message(self, sender: str, text: str):
        msg = QLabel(text)
        msg.setWordWrap(True)
        if sender == "bot":
            msg.setStyleSheet("background: rgba(123, 97, 255, 0.2); border: 1px solid rgba(123, 97, 255, 0.35); border-radius: 10px; padding: 7px 11px; color: #f4f7fb; font-size: 11px;")
        else:
            msg.setStyleSheet("background: #12d8c5; color: #080a0e; font-weight: bold; border-radius: 10px; padding: 7px 11px; font-size: 11px;")
        self.chat_layout.addWidget(msg)

    def _send_message(self):
        txt = self.input_field.text().strip()
        if not txt:
            return
        self._add_message("user", txt)
        self.input_field.clear()
        QTimer.singleShot(350, lambda: self._add_message("bot", f"✓ Understood: '{txt}'. Task ready for UACL execution."))


# =============================================================================
# MAIN QUICK SETTINGS PANEL WINDOW
# =============================================================================

class ControlCenterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(450)
        self.setFixedHeight(560)

        self._init_ui()
        self._sync_state()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._sync_state)
        self.timer.start(4000)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # The Panel
        panel = QFrame(self)
        panel.setStyleSheet("""
            QFrame#panel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(25,30,40,0.98), stop:1 rgba(14,18,25,0.99));
                border: 1px solid #333c49;
                border-radius: 24px;
            }
            QLabel { color: #f4f7fb; font-family: 'Inter'; }
        """)
        panel.setObjectName("panel")

        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 14)
        panel.setGraphicsEffect(shadow)

        p_lay = QVBoxLayout(panel)
        p_lay.setContentsMargins(18, 18, 18, 18)
        p_lay.setSpacing(12)

        # -------------------------------------------------------------
        # 1. HEADER (Quick Settings // Theonix Control Center + Edit)
        # -------------------------------------------------------------
        h_row = QHBoxLayout()
        
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title_lbl = QLabel("Quick Settings")
        title_lbl.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("font-size: 19px; font-weight: 750; letter-spacing: -0.5px;")

        sub_lbl = QLabel("Theonix Control Center")
        sub_lbl.setFont(QFont("Inter", 10))
        sub_lbl.setStyleSheet("color: #9ca7b7; font-size: 12px;")
        t_box.addWidget(title_lbl)
        t_box.addWidget(sub_lbl)

        edit_btn = QPushButton("✎ Edit")
        edit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #333c49;
                background: transparent;
                color: #f4f7fb;
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #242b36; }
        """)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(self._open_settings)

        h_row.addLayout(t_box)
        h_row.addStretch()
        h_row.addWidget(edit_btn)
        p_lay.addLayout(h_row)

        # -------------------------------------------------------------
        # 2. 2-COLUMN GRID (6 TILES)
        # -------------------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(10)

        self.t_wifi = QuickTile("⌁", "Wi-Fi", "Theonix_5G", active=True, has_arrow=True)
        self.t_wifi.toggled.connect(self._toggle_wifi)

        self.t_bt = QuickTile("ᛒ", "Bluetooth", "Connected", active=True, has_arrow=True)
        self.t_bt.toggled.connect(self._toggle_bt)

        self.t_air = QuickTile("✈", "Airplane mode", "Off", active=False)
        self.t_air.toggled.connect(self._toggle_airplane)

        self.t_night = QuickTile("☾", "Night Light", "Off", active=False)
        self.t_night.toggled.connect(lambda a: self.t_night.set_state_text("Warm 4500K" if a else "Off"))

        self.t_bat = QuickTile("▣", "Battery Saver", "On • 78%", active=True)
        self.t_bat.toggled.connect(self._toggle_battery)

        self.t_focus = QuickTile("◉", "Focus", "Off", active=False)
        self.t_focus.toggled.connect(lambda a: self.t_focus.set_state_text("On" if a else "Off"))

        grid.addWidget(self.t_wifi, 0, 0)
        grid.addWidget(self.t_bt, 0, 1)
        grid.addWidget(self.t_air, 1, 0)
        grid.addWidget(self.t_night, 1, 1)
        grid.addWidget(self.t_bat, 2, 0)
        grid.addWidget(self.t_focus, 2, 1)
        p_lay.addLayout(grid)

        # -------------------------------------------------------------
        # 3. CONTROLS (Brightness & Volume)
        # -------------------------------------------------------------
        ctrl_box = QVBoxLayout()
        ctrl_box.setSpacing(10)

        # Brightness Card
        b_card = QFrame()
        b_card.setStyleSheet("background: #202631; border: 1px solid #333c49; border-radius: 16px;")
        b_lay = QVBoxLayout(b_card)
        b_lay.setContentsMargins(14, 12, 14, 12)
        b_lay.setSpacing(8)

        b_top = QHBoxLayout()
        b_t_lbl = QLabel("☼ Brightness")
        b_t_lbl.setStyleSheet("color: #f4f7fb; font-size: 12px; font-weight: 500;")
        self.b_val = QLabel(f"{get_screen_brightness()}%")
        self.b_val.setStyleSheet("color: #f4f7fb; font-size: 12px; font-weight: 750;")
        b_top.addWidget(b_t_lbl)
        b_top.addStretch()
        b_top.addWidget(self.b_val)
        b_lay.addLayout(b_top)

        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(5, 100)
        self.b_slider.setValue(get_screen_brightness())
        self.b_slider.setStyleSheet(self._slider_qss())
        self.b_slider.valueChanged.connect(self._on_bright_changed)
        b_lay.addWidget(self.b_slider)
        ctrl_box.addWidget(b_card)

        # Volume Card
        v_card = QFrame()
        v_card.setStyleSheet("background: #202631; border: 1px solid #333c49; border-radius: 16px;")
        v_lay = QVBoxLayout(v_card)
        v_lay.setContentsMargins(14, 12, 14, 12)
        v_lay.setSpacing(8)

        v_top = QHBoxLayout()
        v_t_lbl = QLabel("🔊 Volume")
        v_t_lbl.setStyleSheet("color: #f4f7fb; font-size: 12px; font-weight: 500;")
        self.v_val = QLabel(f"{get_audio_volume()}%")
        self.v_val.setStyleSheet("color: #f4f7fb; font-size: 12px; font-weight: 750;")
        v_top.addWidget(v_t_lbl)
        v_top.addStretch()
        v_top.addWidget(self.v_val)
        v_lay.addLayout(v_top)

        self.v_slider = QSlider(Qt.Orientation.Horizontal)
        self.v_slider.setRange(0, 150)
        self.v_slider.setValue(get_audio_volume())
        self.v_slider.setStyleSheet(self._slider_qss())
        self.v_slider.valueChanged.connect(self._on_vol_changed)
        v_lay.addWidget(self.v_slider)
        ctrl_box.addWidget(v_card)

        p_lay.addLayout(ctrl_box)

        # -------------------------------------------------------------
        # 4. FOOTER (THAID Status + Settings & Lock Circles)
        # -------------------------------------------------------------
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #333c49; padding-top: 6px;")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 8, 0, 0)
        f_lay.setSpacing(10)

        # THAID Status Clickable area
        st_box = QHBoxLayout()
        st_box.setSpacing(9)

        dot = QLabel()
        dot.setFixedSize(9, 9)
        dot.setStyleSheet("background: #12d8c5; border-radius: 4px; border: 1px solid #12d8c5;")
        dot_shadow = QGraphicsDropShadowEffect(self)
        dot_shadow.setBlurRadius(12)
        dot_shadow.setColor(QColor(18, 216, 197, 200))
        dot_shadow.setOffset(0, 0)
        dot.setGraphicsEffect(dot_shadow)

        st_text = QVBoxLayout()
        st_text.setSpacing(1)
        st_title = QLabel("THAID Ready")
        st_title.setStyleSheet("color: #f4f7fb; font-size: 13px; font-weight: 700;")
        st_sub = QLabel("Local AI • Qwen 3.5 4B")
        st_sub.setStyleSheet("color: #9ca7b7; font-size: 11px;")
        st_text.addWidget(st_title)
        st_text.addWidget(st_sub)

        st_box.addWidget(dot)
        st_box.addLayout(st_text)
        f_lay.addLayout(st_box)
        f_lay.addStretch()

        # Action Circles
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(38, 38)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #202631;
                border: 1px solid #333c49;
                border-radius: 12px;
                color: #f4f7fb;
                font-size: 15px;
            }
            QPushButton:hover { background: #29313d; }
        """)
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self._open_settings)

        lock_btn = QPushButton("⌁")
        lock_btn.setFixedSize(38, 38)
        lock_btn.setStyleSheet("""
            QPushButton {
                background: #202631;
                border: 1px solid #333c49;
                border-radius: 12px;
                color: #f4f7fb;
                font-size: 15px;
            }
            QPushButton:hover { background: #29313d; }
        """)
        lock_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        lock_btn.clicked.connect(self._lock_screen)

        f_lay.addWidget(settings_btn)
        f_lay.addWidget(lock_btn)
        p_lay.addLayout(f_lay)

        main_layout.addWidget(panel)

    def _slider_qss(self) -> str:
        return """
            QSlider::groove:horizontal {
                height: 6px;
                background: #2b333f;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #7b61ff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 2px solid #7b61ff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
        """

    def _sync_state(self):
        wf = get_wifi_status()
        self.t_wifi.set_active(wf["enabled"])
        self.t_wifi.set_state_text(wf["ssid"] if wf["enabled"] else "Off")

        bt = get_bluetooth_status()
        self.t_bt.set_active(bt)
        self.t_bt.set_state_text("Connected" if bt else "Off")

        bat = get_battery_info()
        self.t_bat.set_state_text(f"On • {bat['capacity']}%")

    def _toggle_wifi(self, active: bool):
        toggle_wifi(active)
        self.t_wifi.set_state_text("Connecting..." if active else "Off")

    def _toggle_bt(self, active: bool):
        toggle_bluetooth(active)
        self.t_bt.set_state_text("Connected" if active else "Off")

    def _toggle_airplane(self, active: bool):
        self.t_air.set_state_text("On" if active else "Off")
        if active:
            self._toggle_wifi(False)
            self._toggle_bt(False)
        else:
            self._toggle_wifi(True)
            self._toggle_bt(True)

    def _toggle_battery(self, active: bool):
        bat = get_battery_info()
        self.t_bat.set_state_text(f"On • {bat['capacity']}%" if active else "Off")

    def _on_bright_changed(self, val: int):
        self.b_val.setText(f"{val}%")
        set_screen_brightness(val)

    def _on_vol_changed(self, val: int):
        self.v_val.setText(f"{val}%")
        set_audio_volume(val)

    def _open_settings(self):
        self.hide()
        subprocess.Popen(["theonix-settings"])

    def _lock_screen(self):
        self.hide()
        subprocess.Popen(["loginctl", "lock-session"])

    def _open_thaid(self):
        dlg = ThaidPromptDialog(self)
        dlg.exec()

    def toggle_position(self, tray_pos: QPoint = None):
        if self.isVisible():
            self.hide()
        else:
            screen = QApplication.primaryScreen().geometry()
            if tray_pos and tray_pos.x() > 0:
                x = min(screen.width() - self.width() - 12, max(12, tray_pos.x() - self.width() // 2))
                y = screen.height() - self.height() - 48 if tray_pos.y() > screen.height() // 2 else 48
            else:
                x = screen.width() - self.width() - 16
                y = screen.height() - self.height() - 52
            self.move(x, max(32, y))
            self.show()
            self.raise_()
            self.activateWindow()


# =============================================================================
# D-BUS SERVICE & TASKBAR TRAY
# =============================================================================

class ControlCenterService(QObject):
    toggled = pyqtSignal(bool)

    def __init__(self, window: ControlCenterWindow, tray: QSystemTrayIcon):
        super().__init__()
        self.window = window
        self.tray = tray

    @pyqtSlot(result=bool)
    def Toggle(self) -> bool:
        tray_geom = self.tray.geometry()
        pos = QPoint(tray_geom.center().x(), tray_geom.center().y()) if tray_geom.isValid() else None
        self.window.toggle_position(pos)
        self.toggled.emit(self.window.isVisible())
        return self.window.isVisible()

    @pyqtSlot(result=bool)
    def Show(self) -> bool:
        if not self.window.isVisible():
            self.window.toggle_position()
        return True

    @pyqtSlot(result=bool)
    def Hide(self) -> bool:
        if self.window.isVisible():
            self.window.hide()
        return True

    @pyqtSlot(result=str)
    def GetQuickSettings(self) -> str:
        return json.dumps({
            "wifi": get_wifi_status(),
            "battery": get_battery_info(),
            "volume": get_audio_volume(),
            "brightness": get_screen_brightness(),
            "local_ai": True
        })


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    bus = QDBusConnection.sessionBus()

    win = ControlCenterWindow()

    tray_icon = QSystemTrayIcon(create_tray_icon(), app)
    tray_icon.setToolTip("Theonix Quick Settings")

    menu = QMenu()
    menu.setStyleSheet("""
        QMenu {
            background: #171c24;
            border: 1px solid #333c49;
            border-radius: 8px;
            padding: 4px;
            color: #f4f7fb;
            font-family: 'Inter';
        }
        QMenu::item { padding: 6px 16px; border-radius: 4px; }
        QMenu::item:selected { background: rgba(123, 97, 255, 0.25); color: #7b61ff; }
    """)
    act_open = menu.addAction("🎛️ Quick Settings")
    act_open.triggered.connect(lambda: win.toggle_position())
    
    act_settings = menu.addAction("⚙️ Theonix Settings")
    act_settings.triggered.connect(lambda: subprocess.Popen(["theonix-settings"]))
    
    menu.addSeparator()
    act_quit = menu.addAction("✕ Quit")
    act_quit.triggered.connect(app.quit)

    tray_icon.setContextMenu(menu)
    tray_icon.activated.connect(lambda reason: win.toggle_position(QCursor.pos()) if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray_icon.show()

    service = ControlCenterService(win, tray_icon)

    if not bus.registerService("org.theonix.ControlCenter"):
        print("[ControlCenter] Toggling active instance...")
        from PyQt6.QtDBus import QDBusMessage
        msg = QDBusMessage.createMethodCall("org.theonix.ControlCenter", "/org/theonix/ControlCenter", "", "Toggle")
        bus.call(msg)
        sys.exit(0)

    if not bus.registerObject("/org/theonix/ControlCenter", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        sys.exit(1)

    if "--daemon" not in sys.argv:
        win.toggle_position()

    print("[ControlCenter] Theonix Quick Settings active on taskbar tray.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
