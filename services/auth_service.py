#!/usr/bin/env python3
"""
Theonix OS — Authentication & Permission Approval Service (org.theonix.Auth)
Provides centralized security, credential vault, and interactive THAID authorization prompts.
"""

import sys
import os
import json
import sqlite3
import hashlib
import threading
from typing import Dict, Any

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtDBus import QDBusConnection


AUTH_DB_PATH = os.path.expanduser("~/.config/theonix/auth_vault.db")


class GlassAuthDialog(QDialog):
    """Modern translucent confirmation modal for THAID and system action approvals."""

    def __init__(self, app_name: str, action: str, target: str, risk_level: str):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 240)
        self.approved = False

        self._init_ui(app_name, action, target, risk_level)

        # Auto-reject after 30s of inactivity
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.reject)
        self.timeout_timer.start(30000)

    def _init_ui(self, app_name: str, action: str, target: str, risk_level: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Glass Container
        container = QDialog(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QDialog#container {
                background-color: #0b0f19;
                border: 1.5px solid #00FFAA;
                border-radius: 20px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }
        """)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(12)

        # Header with Security Badge
        h_layout = QHBoxLayout()
        icon_lbl = QLabel("🛡️")
        icon_lbl.setFont(QFont("Inter", 22))
        
        title_lbl = QLabel(f"Authorization Requested")
        title_lbl.setFont(QFont("Inter", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00FFAA;")
        
        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        c_layout.addLayout(h_layout)

        # Detail text
        desc_text = f"<b>{app_name}</b> is requesting permission to:<br><br>" \
                    f"<span style='color: #38BDF8;'>Action:</span> <b>{action}</b><br>" \
                    f"<span style='color: #94A3B8;'>Target:</span> <code>{target}</code>"
        detail_lbl = QLabel(desc_text)
        detail_lbl.setFont(QFont("Inter", 13))
        detail_lbl.setWordWrap(True)
        c_layout.addWidget(detail_lbl)
        c_layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        deny_btn = QPushButton("Deny")
        deny_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        deny_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
                border-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        deny_btn.clicked.connect(self.reject)

        allow_btn = QPushButton("Allow")
        allow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        allow_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFAA, stop:1 #00E5FF);
                color: #050814;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #00FFAA;
            }
        """)
        allow_btn.clicked.connect(self._on_allow)

        btn_layout.addStretch()
        btn_layout.addWidget(deny_btn)
        btn_layout.addWidget(allow_btn)
        c_layout.addLayout(btn_layout)

        layout.addWidget(container)

    def _on_allow(self):
        self.approved = True
        self.accept()


class AuthService(QObject):
    authorizationGranted = pyqtSignal(str, str)   # app, action
    authorizationDenied = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(AUTH_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(AUTH_DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                namespace TEXT,
                key TEXT,
                value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(namespace, key)
            )
        """)
        conn.commit()
        conn.close()

    @pyqtSlot(str, str, str, str, result=bool)
    def RequestAuthorization(self, app_name: str, action: str, target: str, risk_level: str = "CONFIRM") -> bool:
        """Presents an interactive authorization prompt and returns boolean decision."""
        print(f"[AuthService] Prompting approval for {app_name}: {action} on {target}")
        dlg = GlassAuthDialog(app_name, action, target, risk_level)
        dlg.exec()
        
        if dlg.approved:
            self.authorizationGranted.emit(app_name, action)
            return True
        else:
            self.authorizationDenied.emit(app_name, action)
            return False

    @pyqtSlot(str, str, str, result=bool)
    def StoreSecret(self, namespace: str, key: str, value: str) -> bool:
        """Securely saves a credential key-value pair."""
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO credentials (namespace, key, value) VALUES (?, ?, ?)",
                (namespace, key, value)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AuthService] StoreSecret error: {e}")
            return False

    @pyqtSlot(str, str, result=str)
    def GetSecret(self, namespace: str, key: str) -> str:
        """Retrieves a stored secret value."""
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("SELECT value FROM credentials WHERE namespace = ? AND key = ?", (namespace, key))
            row = c.fetchone()
            conn.close()
            return row[0] if row else ""
        except Exception as e:
            print(f"[AuthService] GetSecret error: {e}")
            return ""

    @pyqtSlot(str, str, result=bool)
    def DeleteSecret(self, namespace: str, key: str) -> bool:
        """Deletes a stored secret."""
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM credentials WHERE namespace = ? AND key = ?", (namespace, key))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AuthService] DeleteSecret error: {e}")
            return False


def main():
    app = QApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    service = AuthService()
    if not bus.registerService("org.theonix.Auth"):
        print("[AuthService] Failed to register D-Bus service 'org.theonix.Auth'")
        sys.exit(1)

    if not bus.registerObject("/org/theonix/Auth", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[AuthService] Failed to register D-Bus object at '/org/theonix/Auth'")
        sys.exit(1)

    print("[AuthService] Theonix Authentication Service active on org.theonix.Auth [/org/theonix/Auth]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
