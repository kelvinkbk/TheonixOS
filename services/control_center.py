#!/usr/bin/env python3
"""
Theonix OS — Unified Control Center Service & Quick Settings Drawer (org.theonix.ControlCenter)
Provides Cyber-Obsidian sliding quick-settings drawer for Wi-Fi, Bluetooth, Audio, Brightness,
Performance Profiles, Battery telemetry, Media player, and Local AI status.
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
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QProgressBar, QGraphicsDropShadowEffect, QGridLayout,
    QFrame
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon
from PyQt6.QtDBus import QDBusConnection


def get_battery_info() -> Dict[str, Any]:
    """Reads battery telemetry from sysfs."""
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
    return {"capacity": 100, "status": "Plugged In", "available": False}


def get_wifi_status() -> Dict[str, Any]:
    """Reads Wi-Fi status and active SSID via nmcli."""
    res = {"enabled": True, "ssid": "Connected"}
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


def get_audio_volume() -> int:
    try:
        r = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, timeout=1)
        for part in r.stdout.split():
            if "%" in part:
                return int(part.replace("%", ""))
    except Exception:
        pass
    return 75


def set_audio_volume(vol: int):
    try:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{vol}%"], timeout=1)
    except Exception:
        pass


def toggle_audio_mute():
    try:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], timeout=1)
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
    return 80


def set_screen_brightness(pct: int):
    try:
        backlights = glob.glob("/sys/class/backlight/*")
        if backlights:
            b_dir = backlights[0]
            with open(os.path.join(b_dir, "max_brightness")) as f:
                mx = int(f.read().strip())
            val = max(1, int((pct / 100) * mx))
            # write directly if allowed or use pkexec / brightnessctl
            if shutil.which("brightnessctl"):
                subprocess.run(["brightnessctl", "set", f"{pct}%"], timeout=1)
            else:
                try:
                    with open(os.path.join(b_dir, "brightness"), "w") as f:
                        f.write(str(val))
                except Exception:
                    pass
    except Exception:
        pass


class QuickTile(QFrame):
    """Sleek Cyber-Obsidian toggle tile for quick actions."""
    toggled = pyqtSignal(bool)

    def __init__(self, icon_str: str, title: str, subtitle: str = "", active: bool = False, parent=None):
        super().__init__(parent)
        self.active = active
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(64)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.icon_lbl = QLabel(icon_str)
        self.icon_lbl.setFont(QFont("Inter", 18))
        layout.addWidget(self.icon_lbl)

        v_box = QVBoxLayout()
        v_box.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet("color: #FFFFFF;")

        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setFont(QFont("Inter", 10))
        self.sub_lbl.setStyleSheet("color: #94A3B8;")

        v_box.addWidget(self.title_lbl)
        v_box.addWidget(self.sub_lbl)
        layout.addLayout(v_box)
        layout.addStretch()

        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.active = not self.active
            self._update_style()
            self.toggled.emit(self.active)
        super().mousePressEvent(event)

    def set_subtitle(self, text: str):
        self.sub_lbl.setText(text)

    def set_state(self, active: bool):
        self.active = active
        self._update_style()

    def _update_style(self):
        if self.active:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(0,255,170,0.22), stop:1 rgba(0,229,255,0.15));
                    border: 1.5px solid #00FFAA;
                    border-radius: 12px;
                }
                QLabel { background: transparent; }
            """)
            self.sub_lbl.setStyleSheet("color: #00FFAA; font-weight: 600;")
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.09);
                    border-color: rgba(255, 255, 255, 0.2);
                }
                QLabel { background: transparent; }
            """)
            self.sub_lbl.setStyleSheet("color: #94A3B8;")


class ControlCenterWindow(QWidget):
    """Sliding Cyber-Obsidian Unified Control Center Drawer."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 590)

        self._init_ui()
        self._sync_state()

        # Telemetry refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._sync_state)
        self.timer.start(5000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #f2060913;
                border: 1.5px solid rgba(0, 255, 170, 0.35);
                border-radius: 20px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }
        """)

        # Add drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 255, 170, 60))
        shadow.setOffset(0, 6)
        container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        # 1. Header: User, Battery & Local AI Status
        h_row = QHBoxLayout()
        user_name = os.environ.get("USER", "Theonix User")
        
        user_lbl = QLabel(f"👤 <b>{user_name}</b>")
        user_lbl.setFont(QFont("Inter", 12))
        
        self.ai_badge = QLabel("🟢 Local AI")
        self.ai_badge.setStyleSheet("color: #00FFAA; background: rgba(0,255,170,0.12); border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: bold;")

        self.bat_lbl = QLabel("🔋 100%")
        self.bat_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")

        h_row.addWidget(user_lbl)
        h_row.addStretch()
        h_row.addWidget(self.ai_badge)
        h_row.addWidget(self.bat_lbl)
        c_layout.addLayout(h_row)

        # 2. Quick Action Tiles (2x3 Grid)
        grid = QGridLayout()
        grid.setSpacing(8)

        self.wifi_tile = QuickTile("📶", "Wi-Fi", "Connected", active=True)
        self.wifi_tile.toggled.connect(self._on_wifi_toggled)

        self.bt_tile = QuickTile("🔵", "Bluetooth", "Ready", active=False)
        self.bt_tile.toggled.connect(lambda a: self.bt_tile.set_subtitle("On" if a else "Off"))

        self.perf_tile = QuickTile("⚡", "Performance", "Balanced", active=True)
        self.perf_tile.toggled.connect(self._on_perf_toggled)

        self.night_tile = QuickTile("🌙", "Night Light", "Off", active=False)
        self.night_tile.toggled.connect(lambda a: self.night_tile.set_subtitle("Warm 4500K" if a else "Off"))

        self.vpn_tile = QuickTile("🛡️", "VPN", "Idle", active=False)
        self.vpn_tile.toggled.connect(lambda a: self.vpn_tile.set_subtitle("Secured" if a else "Idle"))

        self.thaid_tile = QuickTile("🤖", "THAID Orb", "Visible", active=True)
        self.thaid_tile.toggled.connect(self._on_thaid_toggled)

        grid.addWidget(self.wifi_tile, 0, 0)
        grid.addWidget(self.bt_tile, 0, 1)
        grid.addWidget(self.perf_tile, 1, 0)
        grid.addWidget(self.night_tile, 1, 1)
        grid.addWidget(self.vpn_tile, 2, 0)
        grid.addWidget(self.thaid_tile, 2, 1)
        c_layout.addLayout(grid)

        # 3. Interactive Sliders (Brightness & Volume)
        slider_box = QVBoxLayout()
        slider_box.setSpacing(10)

        # Brightness
        b_row = QHBoxLayout()
        b_icon = QLabel("☀️")
        b_icon.setFont(QFont("Inter", 14))
        self.b_slider = QSlider(Qt.Orientation.Horizontal)
        self.b_slider.setRange(5, 100)
        self.b_slider.setValue(get_screen_brightness())
        self.b_slider.setStyleSheet(self._slider_qss("#00FFAA"))
        self.b_lbl = QLabel(f"{self.b_slider.value()}%")
        self.b_lbl.setFixedWidth(36)
        self.b_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.b_slider.valueChanged.connect(self._on_brightness_changed)

        b_row.addWidget(b_icon)
        b_row.addWidget(self.b_slider)
        b_row.addWidget(self.b_lbl)
        slider_box.addLayout(b_row)

        # Volume
        v_row = QHBoxLayout()
        self.v_btn = QPushButton("🔊")
        self.v_btn.setStyleSheet("background: transparent; border: none; font-size: 14px;")
        self.v_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.v_btn.clicked.connect(self._on_mute_clicked)

        self.v_slider = QSlider(Qt.Orientation.Horizontal)
        self.v_slider.setRange(0, 150)
        self.v_slider.setValue(get_audio_volume())
        self.v_slider.setStyleSheet(self._slider_qss("#38BDF8"))
        self.v_lbl = QLabel(f"{self.v_slider.value()}%")
        self.v_lbl.setFixedWidth(36)
        self.v_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.v_slider.valueChanged.connect(self._on_volume_changed)

        v_row.addWidget(self.v_btn)
        v_row.addWidget(self.v_slider)
        v_row.addWidget(self.v_lbl)
        slider_box.addLayout(v_row)

        c_layout.addLayout(slider_box)

        # 4. Mini Media Player Card
        media_card = QFrame()
        media_card.setStyleSheet("background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 6px;")
        m_layout = QHBoxLayout(media_card)
        m_layout.setContentsMargins(8, 4, 8, 4)
        
        m_art = QLabel("🎵")
        m_art.setFont(QFont("Inter", 16))
        
        m_info = QVBoxLayout()
        m_title = QLabel("Theonix Ambient Audio")
        m_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        m_artist = QLabel("Local Media Player")
        m_artist.setFont(QFont("Inter", 10))
        m_artist.setStyleSheet("color: #94A3B8;")
        m_info.addWidget(m_title)
        m_info.addWidget(m_artist)

        m_btn_play = QPushButton("▶")
        m_btn_play.setFixedSize(28, 28)
        m_btn_play.setStyleSheet("background: rgba(0,255,170,0.2); color: #00FFAA; border-radius: 14px; font-weight: bold; border: none;")

        m_layout.addWidget(m_art)
        m_layout.addLayout(m_info)
        m_layout.addStretch()
        m_layout.addWidget(m_btn_play)
        c_layout.addWidget(media_card)

        # 5. Footer Quick Launchers
        f_row = QHBoxLayout()
        f_row.setSpacing(8)

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setStyleSheet(self._btn_qss())
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self._open_settings)

        lock_btn = QPushButton("🔒 Lock")
        lock_btn.setStyleSheet(self._btn_qss())
        lock_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        lock_btn.clicked.connect(self._lock_screen)

        power_btn = QPushButton("⏻ Power")
        power_btn.setStyleSheet(self._btn_qss(danger=True))
        power_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        power_btn.clicked.connect(self._open_power_menu)

        f_row.addWidget(settings_btn)
        f_row.addWidget(lock_btn)
        f_row.addWidget(power_btn)
        c_layout.addLayout(f_row)

        layout.addWidget(container)

    def _slider_qss(self, accent_color: str) -> str:
        return f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }}
            QSlider::sub-page:horizontal {{
                background: {accent_color};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #FFFFFF;
                border: 2px solid {accent_color};
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }}
        """

    def _btn_qss(self, danger: bool = False) -> str:
        if danger:
            return """
                QPushButton {
                    background: rgba(239, 68, 68, 0.15);
                    color: #F87171;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
                QPushButton:hover { background: rgba(239, 68, 68, 0.35); color: #FFFFFF; }
            """
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 11.5px;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.18); }
        """

    def _sync_state(self):
        # Battery
        bat = get_battery_info()
        self.bat_lbl.setText(f"🔋 {bat['capacity']}%")

        # Wi-Fi
        wf = get_wifi_status()
        self.wifi_tile.set_state(wf["enabled"])
        self.wifi_tile.set_subtitle(wf["ssid"] if wf["enabled"] else "Off")

    def _on_wifi_toggled(self, active: bool):
        toggle_wifi(active)
        self.wifi_tile.set_subtitle("Scanning..." if active else "Off")

    def _on_perf_toggled(self, active: bool):
        modes = ["Power Saver", "Balanced", "Performance"]
        curr = self.perf_tile.sub_lbl.text()
        nxt = modes[(modes.index(curr) + 1) % len(modes)] if curr in modes else "Balanced"
        self.perf_tile.set_subtitle(nxt)

    def _on_thaid_toggled(self, active: bool):
        self.thaid_tile.set_subtitle("Visible" if active else "Hidden")
        try:
            subprocess.Popen(["thaid-gui"])
        except Exception:
            pass

    def _on_brightness_changed(self, val: int):
        self.b_lbl.setText(f"{val}%")
        set_screen_brightness(val)

    def _on_volume_changed(self, val: int):
        self.v_lbl.setText(f"{val}%")
        set_audio_volume(val)

    def _on_mute_clicked(self):
        toggle_audio_mute()
        self.v_slider.setValue(get_audio_volume())

    def _open_settings(self):
        self.hide()
        subprocess.Popen(["theonix-settings"])

    def _lock_screen(self):
        self.hide()
        subprocess.Popen(["loginctl", "lock-session"])

    def _open_power_menu(self):
        self.hide()
        try:
            subprocess.Popen(["qdbus", "org.kde.ksmserver", "/KSMServer", "org.kde.KSMServerInterface.logout", "0", "0", "0"])
        except Exception:
            pass

    def toggle_position(self):
        if self.isVisible():
            self.hide()
        else:
            screen = QApplication.primaryScreen().geometry()
            # Position at top-right below standard panel
            self.move(screen.width() - self.width() - 16, 44)
            self.show()
            self.raise_()
            self.activateWindow()


class ControlCenterService(QObject):
    toggled = pyqtSignal(bool)

    def __init__(self, window: ControlCenterWindow):
        super().__init__()
        self.window = window

    @pyqtSlot(result=bool)
    def Toggle(self) -> bool:
        self.window.toggle_position()
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
    bus = QDBusConnection.sessionBus()

    win = ControlCenterWindow()
    service = ControlCenterService(win)

    if not bus.registerService("org.theonix.ControlCenter"):
        print("[ControlCenter] Already running or failed to register 'org.theonix.ControlCenter'. Toggling active instance...")
        # Toggle existing instance over D-Bus
        from PyQt6.QtDBus import QDBusMessage
        msg = QDBusMessage.createMethodCall("org.theonix.ControlCenter", "/org/theonix/ControlCenter", "", "Toggle")
        bus.call(msg)
        sys.exit(0)

    if not bus.registerObject("/org/theonix/ControlCenter", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[ControlCenter] Failed to register D-Bus object at '/org/theonix/ControlCenter'")
        sys.exit(1)

    # If run directly as CLI toggle, show immediately
    if "--daemon" not in sys.argv:
        win.toggle_position()

    print("[ControlCenter] Theonix Unified Control Center active on org.theonix.ControlCenter [/org/theonix/ControlCenter]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
