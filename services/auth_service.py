#!/usr/bin/env python3
"""
Theonix OS — Authentication & Passkey Service (org.theonix.Auth)
Provides centralized security, credential vault, WebAuthn/FIDO2 Passkey engine,
interactive Passkey/password verification dialogs, and PAM authentication.
"""

import sys
import os
import time
import json
import base64
import sqlite3
import hashlib
import secrets
import subprocess
from typing import Dict, Any, List

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtDBus import QDBusConnection

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization


AUTH_DB_PATH = os.path.expanduser("~/.config/theonix/auth_vault.db")


def verify_system_password(password: str) -> bool:
    """Verifies user password against system PAM authentication."""
    if not password:
        return False
    try:
        proc = subprocess.run(
            ["sudo", "-k", "-S", "true"],
            input=password + "\n",
            capture_output=True,
            text=True,
            timeout=3
        )
        return proc.returncode == 0
    except Exception:
        return False


class GlassAuthDialog(QDialog):
    """Modern translucent confirmation modal with Passkey and Password verification."""

    def __init__(self, app_name: str, action: str, target: str, risk_level: str):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 290)
        self.approved = False

        self._init_ui(app_name, action, target, risk_level)

        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.reject)
        self.timeout_timer.start(45000)

    def _init_ui(self, app_name: str, action: str, target: str, risk_level: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #f2060913;
                border: 1.5px solid #00FFAA;
                border-radius: 20px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }
        """)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(22, 18, 22, 18)
        c_layout.setSpacing(10)

        # Header with Security Badge
        h_layout = QHBoxLayout()
        icon_lbl = QLabel("🛡️")
        icon_lbl.setFont(QFont("Inter", 20))
        
        title_lbl = QLabel("Authorization Requested")
        title_lbl.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00FFAA;")
        
        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        c_layout.addLayout(h_layout)

        # Detail text
        desc_text = f"<b>{app_name}</b> is requesting permission to:<br>" \
                    f"<span style='color: #38BDF8;'>Action:</span> <b>{action}</b> &nbsp;|&nbsp; " \
                    f"<span style='color: #94A3B8;'>Target:</span> <code>{target}</code>"
        detail_lbl = QLabel(desc_text)
        detail_lbl.setFont(QFont("Inter", 12))
        detail_lbl.setWordWrap(True)
        c_layout.addWidget(detail_lbl)

        # Password / PIN Fallback field
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Enter system password or PIN (optional)...")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #00FFAA;
            }
        """)
        self.pwd_input.returnPressed.connect(self._on_password_submit)
        c_layout.addWidget(self.pwd_input)

        self.status_msg = QLabel("")
        self.status_msg.setStyleSheet("font-size: 11px;")
        c_layout.addWidget(self.status_msg)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        deny_btn = QPushButton("Deny")
        deny_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        deny_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
                border-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        deny_btn.clicked.connect(self.reject)

        allow_btn = QPushButton("Authorize")
        allow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        allow_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FFAA, stop:1 #00E5FF);
                color: #050814;
                border: none;
                border-radius: 8px;
                padding: 8px 22px;
                font-size: 12px;
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

    def _on_password_submit(self):
        pwd = self.pwd_input.text().strip()
        if pwd:
            if verify_system_password(pwd):
                self.approved = True
                self.status_msg.setText("✓ Password verified!")
                self.status_msg.setStyleSheet("color: #00FFAA; font-size: 11px;")
                QTimer.singleShot(300, self.accept)
            else:
                self.status_msg.setText("❌ Incorrect password, please try again.")
                self.status_msg.setStyleSheet("color: #EF4444; font-size: 11px;")
        else:
            self._on_allow()

    def _on_allow(self):
        pwd = self.pwd_input.text().strip()
        if pwd and not verify_system_password(pwd):
            self.status_msg.setText("❌ Incorrect password.")
            self.status_msg.setStyleSheet("color: #EF4444; font-size: 11px;")
            return
        self.approved = True
        self.accept()


class GlassPasskeyDialog(QDialog):
    """Interactive modal prompt for Passkey creation and biometric/password confirmation."""

    def __init__(self, mode: str, rp_id: str, user_name: str):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 260)
        self.confirmed = False

        self._init_ui(mode, rp_id, user_name)

    def _init_ui(self, mode: str, rp_id: str, user_name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        container = QWidget(self)
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #f5060913;
                border: 1.5px solid #A855F7;
                border-radius: 18px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }
        """)

        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(20, 18, 20, 18)
        c_layout.setSpacing(8)

        # Header
        h_row = QHBoxLayout()
        icon = QLabel("🔑")
        icon.setFont(QFont("Inter", 20))
        
        title_text = "Create Passkey" if mode == "create" else "Sign in with Passkey"
        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #C084FC;")
        
        h_row.addWidget(icon)
        h_row.addWidget(title_lbl)
        h_row.addStretch()
        c_layout.addLayout(h_row)

        # Details
        info_text = f"<b>Website / App:</b> <span style='color: #00FFAA;'>{rp_id}</span> &nbsp;|&nbsp; " \
                    f"<b>Account:</b> <span style='color: #94A3B8;'>{user_name}</span>"
        info_lbl = QLabel(info_text)
        info_lbl.setFont(QFont("Inter", 12))
        c_layout.addWidget(info_lbl)

        # Password / PIN unlock field
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Enter system password or PIN to unlock passkey...")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 6px 12px;
                color: #FFFFFF;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #A855F7;
            }
        """)
        self.pwd_input.returnPressed.connect(self._on_password_submit)
        c_layout.addWidget(self.pwd_input)

        self.status_msg = QLabel("")
        self.status_msg.setStyleSheet("font-size: 11px;")
        c_layout.addWidget(self.status_msg)

        # Buttons
        b_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        action_btn_text = "Save Passkey" if mode == "create" else "Use Passkey"
        confirm_btn = QPushButton(action_btn_text)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #A855F7, stop:1 #6366F1);
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #A855F7;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)

        b_row.addStretch()
        b_row.addWidget(cancel_btn)
        b_row.addWidget(confirm_btn)
        c_layout.addLayout(b_row)

        layout.addWidget(container)

    def _on_password_submit(self):
        pwd = self.pwd_input.text().strip()
        if pwd:
            if verify_system_password(pwd):
                self.confirmed = True
                self.status_msg.setText("✓ Password verified! Unlocking Passkey...")
                self.status_msg.setStyleSheet("color: #00FFAA; font-size: 11px;")
                QTimer.singleShot(300, self.accept)
            else:
                self.status_msg.setText("❌ Incorrect password.")
                self.status_msg.setStyleSheet("color: #EF4444; font-size: 11px;")
        else:
            self._on_confirm()

    def _on_confirm(self):
        pwd = self.pwd_input.text().strip()
        if pwd and not verify_system_password(pwd):
            self.status_msg.setText("❌ Incorrect password.")
            self.status_msg.setStyleSheet("color: #EF4444; font-size: 11px;")
            return
        self.confirmed = True
        self.accept()


class AuthService(QObject):
    authorizationGranted = pyqtSignal(str, str)
    authorizationDenied = pyqtSignal(str, str)
    passkeyCreated = pyqtSignal(str, str)
    passkeyAuthenticated = pyqtSignal(str, str)

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS passkeys (
                id TEXT PRIMARY KEY,
                rp_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                user_handle TEXT,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                sign_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        """)
        conn.commit()
        conn.close()

    # ---- 1. PAM Password Verification ----
    @pyqtSlot(str, result=bool)
    def VerifyPassword(self, password: str) -> bool:
        """Validates a password against system PAM credentials."""
        return verify_system_password(password)

    # ---- 2. THAID & System Action Authorization ----
    @pyqtSlot(str, str, str, str, result=bool)
    def RequestAuthorization(self, app_name: str, action: str, target: str, risk_level: str = "CONFIRM") -> bool:
        dlg = GlassAuthDialog(app_name, action, target, risk_level)
        dlg.exec()
        if dlg.approved:
            self.authorizationGranted.emit(app_name, action)
            return True
        else:
            self.authorizationDenied.emit(app_name, action)
            return False

    # ---- 3. Keyring Credential Vault ----
    @pyqtSlot(str, str, str, result=bool)
    def StoreSecret(self, namespace: str, key: str, value: str) -> bool:
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

    # ---- 4. WebAuthn / FIDO2 Passkey Engine ----
    @pyqtSlot(str, str, str, result=str)
    def CreatePasskey(self, rp_id: str, user_name: str, user_display_name: str = "") -> str:
        dlg = GlassPasskeyDialog("create", rp_id, user_name)
        dlg.exec()
        if not dlg.confirmed:
            return json.dumps({"success": False, "error": "Passkey registration cancelled by user."})

        try:
            private_key = ec.generate_private_key(ec.SECP256R1())
            public_key = private_key.public_key()

            priv_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")

            pub_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode("utf-8")

            passkey_id = secrets.token_urlsafe(32)
            user_handle = secrets.token_hex(16)

            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO passkeys (id, rp_id, user_name, user_handle, public_key, private_key, sign_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (passkey_id, rp_id, user_name, user_handle, pub_pem, priv_pem))
            conn.commit()
            conn.close()

            self.passkeyCreated.emit(rp_id, user_name)
            return json.dumps({
                "success": True,
                "credential_id": passkey_id,
                "rp_id": rp_id,
                "user_name": user_name,
                "public_key_pem": pub_pem,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def AuthenticatePasskey(self, rp_id: str, challenge: str) -> str:
        conn = sqlite3.connect(AUTH_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, user_name, private_key, sign_count FROM passkeys WHERE rp_id = ? ORDER BY last_used DESC LIMIT 1", (rp_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return json.dumps({"success": False, "error": f"No Passkey found for {rp_id}"})

        passkey_id, user_name, priv_pem, sign_count = row

        dlg = GlassPasskeyDialog("auth", rp_id, user_name)
        dlg.exec()
        if not dlg.confirmed:
            return json.dumps({"success": False, "error": "Passkey authentication cancelled."})

        try:
            private_key = serialization.load_pem_private_key(priv_pem.encode("utf-8"), password=None)
            signature = private_key.sign(challenge.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
            sig_b64 = base64.b64encode(signature).decode("utf-8")

            new_count = sign_count + 1
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE passkeys SET sign_count = ?, last_used = CURRENT_TIMESTAMP WHERE id = ?", (new_count, passkey_id))
            conn.commit()
            conn.close()

            self.passkeyAuthenticated.emit(rp_id, user_name)
            return json.dumps({
                "success": True,
                "credential_id": passkey_id,
                "user_name": user_name,
                "signature_b64": sig_b64,
                "sign_count": new_count
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @pyqtSlot(result=str)
    def ListPasskeys(self) -> str:
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, rp_id, user_name, created_at, last_used, sign_count FROM passkeys ORDER BY created_at DESC")
            rows = c.fetchall()
            conn.close()
            keys = [
                {
                    "id": r[0],
                    "rp_id": r[1],
                    "user_name": r[2],
                    "created_at": r[3],
                    "last_used": r[4] or "Never",
                    "sign_count": r[5]
                }
                for r in rows
            ]
            return json.dumps(keys)
        except Exception:
            return json.dumps([])

    @pyqtSlot(str, result=bool)
    def DeletePasskey(self, passkey_id: str) -> bool:
        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM passkeys WHERE id = ?", (passkey_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AuthService] DeletePasskey error: {e}")
            return False

    @pyqtSlot(result=str)
    def DetectAuthenticators(self) -> str:
        known_vendors = {
            "1050": "Yubico (YubiKey FIDO2 / U2F)",
            "096e": "Feitian (ePass FIDO2 Token)",
            "18d1": "Google Titan Security Key",
            "20a0": "Nitrokey (FIDO2 / OpenPGP)",
            "1209": "SoloKeys / Hacker FIDO2",
            "4b42": "SoloKeys Solo 2",
            "2581": "Ledger / U2F Token",
            "1e0d": "Canokey FIDO2"
        }

        detected_hardware = []
        try:
            res = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=2)
            for line in res.stdout.splitlines():
                for vid, vname in known_vendors.items():
                    if f"ID {vid}:" in line.lower() or f"{vid}:" in line:
                        detected_hardware.append({
                            "vendor_id": vid,
                            "name": vname,
                            "raw_desc": line.strip()
                        })
        except Exception:
            pass

        data = {
            "platform_authenticator": {
                "available": True,
                "name": "Theonix Cryptographic Vault",
                "algorithm": "ECDSA SECP256R1 (P-256)",
                "status": "Active & Ready"
            },
            "hardware_security_keys": detected_hardware,
            "hardware_key_connected": len(detected_hardware) > 0,
            "total_passkeys_stored": 0
        }

        try:
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM passkeys")
            data["total_passkeys_stored"] = c.fetchone()[0]
            conn.close()
        except Exception:
            pass

        return json.dumps(data)


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

    print("[AuthService] Theonix Authentication & Passkey Service active on org.theonix.Auth [/org/theonix/Auth]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
