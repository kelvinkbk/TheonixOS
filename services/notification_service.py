#!/usr/bin/env python3
"""
Theonix OS — Unified Notification Service (org.theonix.Notifications)
Provides glassmorphism desktop notification overlays, priority action dispatch, and history center.
"""

import sys
import os
import time
import json
import subprocess
import threading
from typing import Dict, Any, List

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtDBus import QDBusConnection


APP_ACCENT_COLORS = {
    "thaid": "#00FFAA",
    "theonix browser": "#00E5FF",
    "theonix messages": "#A855F7",
    "theonix store": "#C084FC",
    "theonix files": "#38BDF8",
    "system": "#F59E0B",
    "default": "#00FFAA"
}


class GlassNotificationBanner(QWidget):
    """Sleek top-right glass notification card with smooth slide animation."""

    def __init__(self, notif_id: int, app_name: str, title: str, message: str, icon_str: str, 
                 actions: List[str], timeout_ms: int, on_action_cb, on_close_cb, stack_index: int = 0):
        super().__init__()
        self.notif_id = notif_id
        self.on_action_cb = on_action_cb
        self.on_close_cb = on_close_cb
        self.stack_index = stack_index

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.SubWindow |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(380, 110)

        # Positioning at Top-Right
        screen = QApplication.primaryScreen().geometry()
        self.target_x = screen.width() - self.width() - 24
        self.target_y = 48 + (stack_index * 120)
        self.move(self.target_x + 60, self.target_y)

        accent = APP_ACCENT_COLORS.get(app_name.lower(), APP_ACCENT_COLORS["default"])
        self._init_ui(app_name, title, message, icon_str, actions, accent)

        # Slide-in Animation
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(350)
        self.pos_anim.setStartValue(QPoint(self.target_x + 60, self.target_y))
        self.pos_anim.setEndValue(QPoint(self.target_x, self.target_y))
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.pos_anim.start()

        # Auto-dismiss timer
        if timeout_ms > 0:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.dismiss)
            self.timer.start(timeout_ms)

    def _init_ui(self, app_name: str, title: str, message: str, icon_str: str, actions: List[str], accent: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Glass Container
        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background-color: #f2060913;
                border: 1px solid {accent}66;
                border-left: 3px solid {accent};
                border-radius: 16px;
            }}
            QLabel {{
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }}
        """)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(4)

        # Header Row (App Name, Icon, Close button)
        h_row = QHBoxLayout()
        icon_display = icon_str if icon_str else "🔔"
        app_lbl = QLabel(f"{icon_display}  <b>{app_name.upper()}</b>")
        app_lbl.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        app_lbl.setStyleSheet(f"color: {accent}; letter-spacing: 0.5px;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.dismiss)

        h_row.addWidget(app_lbl)
        h_row.addStretch()
        h_row.addWidget(close_btn)
        c_layout.addLayout(h_row)

        # Title
        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        t_lbl.setStyleSheet("color: #FFFFFF;")
        c_layout.addWidget(t_lbl)

        # Body Message
        b_lbl = QLabel(message)
        b_lbl.setFont(QFont("Inter", 11))
        b_lbl.setStyleSheet("color: #94A3B8;")
        b_lbl.setWordWrap(True)
        c_layout.addWidget(b_lbl)

        # Action Buttons (if any)
        if actions:
            act_row = QHBoxLayout()
            act_row.setSpacing(8)
            for act in actions[:2]:
                btn = QPushButton(act)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255, 255, 255, 0.08);
                        color: #E2E8F0;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 6px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: {accent}33;
                        border-color: {accent};
                        color: #FFFFFF;
                    }}
                """)
                btn.clicked.connect(lambda checked, a=act: self._on_action(a))
                act_row.addWidget(btn)
            act_row.addStretch()
            c_layout.addLayout(act_row)

        layout.addWidget(container)

    def _on_action(self, action_key: str):
        if self.on_action_cb:
            self.on_action_cb(self.notif_id, action_key)
        self.dismiss()

    def dismiss(self):
        # Slide out
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(250)
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(self.target_x + 80, self.target_y))
        self.pos_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.pos_anim.finished.connect(self._finish_close)
        self.pos_anim.start()

    def _finish_close(self):
        if self.on_close_cb:
            self.on_close_cb(self.notif_id)
        self.close()
        self.deleteLater()


class NotificationService(QObject):
    actionInvoked = pyqtSignal(int, str)       # notif_id, action_key
    notificationClosed = pyqtSignal(int, int)  # notif_id, reason (1: expired, 2: dismissed, 3: action)

    def __init__(self):
        super().__init__()
        self._current_id = 100
        self._active_banners: Dict[int, GlassNotificationBanner] = {}
        self._history: List[Dict[str, Any]] = []

    @pyqtSlot(str, str, str, str, str, str, int, result=int)
    def Notify(self, app_name: str, title: str, message: str, icon_str: str = "", 
               priority: str = "normal", actions_json: str = "[]", timeout_ms: int = 6000) -> int:
        """Emits a rich Theonix desktop notification banner."""
        self._current_id += 1
        notif_id = self._current_id

        try:
            actions = json.loads(actions_json) if actions_json else []
        except Exception:
            actions = []

        notif_entry = {
            "id": notif_id,
            "app_name": app_name,
            "title": title,
            "message": message,
            "icon": icon_str,
            "priority": priority,
            "actions": actions,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._history.append(notif_entry)
        if len(self._history) > 100:
            self._history.pop(0)

        # Play subtle interaction chime
        threading.Thread(target=self._play_chime, daemon=True).start()

        # Display on UI thread
        def _show():
            stack_idx = len(self._active_banners)
            banner = GlassNotificationBanner(
                notif_id=notif_id,
                app_name=app_name,
                title=title,
                message=message,
                icon_str=icon_str,
                actions=actions,
                timeout_ms=timeout_ms,
                on_action_cb=self._handle_action,
                on_close_cb=self._handle_close,
                stack_index=stack_idx
            )
            self._active_banners[notif_id] = banner
            banner.show()

        QTimer.singleShot(0, _show)
        return notif_id

    def _handle_action(self, notif_id: int, action_key: str):
        self.actionInvoked.emit(notif_id, action_key)

    def _handle_close(self, notif_id: int):
        if notif_id in self._active_banners:
            del self._active_banners[notif_id]
        self.notificationClosed.emit(notif_id, 2)

    def _play_chime(self):
        try:
            subprocess.run(
                ["speaker-test", "-t", "sine", "-f", "880", "-l", "1", "-s", "1"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.15
            )
        except Exception:
            pass

    @pyqtSlot(int)
    def CloseNotification(self, notif_id: int):
        if notif_id in self._active_banners:
            self._active_banners[notif_id].dismiss()

    @pyqtSlot(result=str)
    def GetHistory(self) -> str:
        return json.dumps(self._history)

    @pyqtSlot()
    def ClearHistory(self):
        self._history.clear()


def main():
    app = QApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    service = NotificationService()
    if not bus.registerService("org.theonix.Notifications"):
        print("[NotificationService] Failed to register D-Bus service 'org.theonix.Notifications'")
        sys.exit(1)

    if not bus.registerObject("/org/theonix/Notifications", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[NotificationService] Failed to register D-Bus object at '/org/theonix/Notifications'")
        sys.exit(1)

    print("[NotificationService] Theonix Notification Service active on org.theonix.Notifications [/org/theonix/Notifications]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
