"""
Theonix Browser — Web View & Page Engine.
Provides Chromium-based QtWebEngine integration, JS content extraction for THAID,
permissions routing, and native WebAuthn / FIDO2 Passkey bridge to org.theonix.Auth.
"""

import os
import json
import base64
import struct
import hashlib
from typing import Callable
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject, pyqtSlot, QFile, QIODevice
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QMessageBox

HAS_WEBENGINE = False
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineScript
    )
    from PyQt6.QtWebChannel import QWebChannel
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    HAS_WEBENGINE = True
except ImportError:
    pass


def get_qwebchannel_js() -> str:
    """Reads Qt's built-in qwebchannel.js resource."""
    try:
        f = QFile(":/qtwebchannel/qwebchannel.js")
        if f.open(QIODevice.OpenModeFlag.ReadOnly):
            content = bytes(f.readAll()).decode("utf-8")
            f.close()
            return content
    except Exception:
        pass
    return ""


def build_fido2_auth_data(rp_id: str, cred_id_bytes: bytes, pub_key_ec) -> bytes:
    """Constructs compliant FIDO2/WebAuthn AuthenticatorData with Attested Credential Data."""
    rp_id_hash = hashlib.sha256(rp_id.encode()).digest()
    flags = b"\x45"  # User Present (0x01) + User Verified (0x04) + Attested Credential Data (0x40)
    sign_count = struct.pack(">I", 1)
    aaguid = b"\x00" * 16
    cred_len = struct.pack(">H", len(cred_id_bytes))

    # COSE Key representation for ECDSA P-256 (ES256)
    numbers = pub_key_ec.public_numbers()
    x_bytes = numbers.x.to_bytes(32, "big")
    y_bytes = numbers.y.to_bytes(32, "big")

    cose_key = (
        b"\xa5\x01\x02\x03\x26\x20\x01"
        b"\x21\x58\x20" + x_bytes +
        b"\x22\x58\x20" + y_bytes
    )

    return rp_id_hash + flags + sign_count + aaguid + cred_len + cred_id_bytes + cose_key


def build_attestation_object(auth_data: bytes) -> bytes:
    """Constructs compliant CBOR AttestationObject map."""
    header = b"\xa3\x63fmt\x64none\x67attStmt\xa0\x68authData"
    if len(auth_data) < 256:
        len_prefix = b"\x58" + struct.pack(">B", len(auth_data))
    else:
        len_prefix = b"\x59" + struct.pack(">H", len(auth_data))
    return header + len_prefix + auth_data


class WebAuthnBridge(QObject):
    """Bridges WebAuthn (navigator.credentials) JavaScript calls directly to Theonix Auth Service."""

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str, str, str, result=str)
    def createCredential(self, rp_id: str, user_name: str, challenge_b64: str) -> str:
        try:
            from theonix_core import AuthClient
            res = AuthClient.create_passkey(rp_id, user_name)
            if not res.get("success"):
                return json.dumps({"success": False, "error": res.get("error", "Passkey creation cancelled.")})

            cred_id = res.get("credential_id", "")
            pub_pem = res.get("public_key_pem", "")

            # Load public key to build compliant COSE Attestation Object
            pub_key = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
            auth_data = build_fido2_auth_data(rp_id, cred_id.encode("utf-8"), pub_key)
            attestation_obj = build_attestation_object(auth_data)

            client_data = json.dumps({
                "type": "webauthn.create",
                "challenge": challenge_b64,
                "origin": f"https://{rp_id}",
                "crossOrigin": False
            })

            return json.dumps({
                "success": True,
                "id": cred_id,
                "rawId_b64": base64.b64encode(cred_id.encode("utf-8")).decode("utf-8"),
                "clientDataJSON_b64": base64.b64encode(client_data.encode("utf-8")).decode("utf-8"),
                "attestationObject_b64": base64.b64encode(attestation_obj).decode("utf-8"),
                "type": "public-key"
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @pyqtSlot(str, str, result=str)
    def getAssertion(self, rp_id: str, challenge_b64: str) -> str:
        try:
            from theonix_core import AuthClient
            res = AuthClient.authenticate_passkey(rp_id, challenge_b64)
            if not res.get("success"):
                return json.dumps({"success": False, "error": res.get("error", "Passkey authentication cancelled.")})

            cred_id = res.get("credential_id", "")
            sig_b64 = res.get("signature_b64", "")

            client_data = json.dumps({
                "type": "webauthn.get",
                "challenge": challenge_b64,
                "origin": f"https://{rp_id}",
                "crossOrigin": False
            })

            # AuthenticatorData for assertion (37 bytes: rpIdHash (32) + flags (1 = 0x05) + signCount (4))
            rp_hash = hashlib.sha256(rp_id.encode()).digest()
            auth_data = rp_hash + b"\x05" + struct.pack(">I", res.get("sign_count", 1))

            return json.dumps({
                "success": True,
                "id": cred_id,
                "rawId_b64": base64.b64encode(cred_id.encode("utf-8")).decode("utf-8"),
                "clientDataJSON_b64": base64.b64encode(client_data.encode("utf-8")).decode("utf-8"),
                "authenticatorData_b64": base64.b64encode(auth_data).decode("utf-8"),
                "signature_b64": sig_b64,
                "userHandle_b64": base64.b64encode(b"user").decode("utf-8"),
                "type": "public-key"
            })
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})


WEBAUTHN_INJECTION_JS = """
(function() {
    function b64ToBuf(b64) {
        let bin = atob(b64);
        let buf = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        return buf.buffer;
    }
    function bufToB64(buf) {
        let bin = '';
        let bytes = new Uint8Array(buf);
        for (let i = 0; i < bytes.byteLength; i++) bin += String.fromCharCode(bytes[i]);
        return btoa(bin);
    }

    if (!navigator.credentials) navigator.credentials = {};

    navigator.credentials.create = async function(options) {
        if (!options || !options.publicKey) return null;
        let pk = options.publicKey;
        let rpId = pk.rp ? (pk.rp.id || window.location.hostname) : window.location.hostname;
        let userName = pk.user ? (pk.user.name || pk.user.displayName || "User") : "User";
        let challengeB64 = pk.challenge ? bufToB64(pk.challenge) : "challenge";

        return new Promise((resolve, reject) => {
            if (!window.webauthnBridge) {
                reject(new DOMException("Theonix Passkey Service unavailable", "NotAllowedError"));
                return;
            }
            window.webauthnBridge.createCredential(rpId, userName, challengeB64, function(resJson) {
                let res = JSON.parse(resJson);
                if (!res.success) {
                    reject(new DOMException(res.error || "User cancelled", "NotAllowedError"));
                    return;
                }
                let cred = {
                    id: res.id,
                    rawId: b64ToBuf(res.rawId_b64),
                    type: 'public-key',
                    response: {
                        clientDataJSON: b64ToBuf(res.clientDataJSON_b64),
                        attestationObject: b64ToBuf(res.attestationObject_b64)
                    },
                    getClientExtensionResults: () => ({})
                };
                resolve(cred);
            });
        });
    };

    navigator.credentials.get = async function(options) {
        if (!options || !options.publicKey) return null;
        let pk = options.publicKey;
        let rpId = pk.rpId || window.location.hostname;
        let challengeB64 = pk.challenge ? bufToB64(pk.challenge) : "challenge";

        return new Promise((resolve, reject) => {
            if (!window.webauthnBridge) {
                reject(new DOMException("Theonix Passkey Service unavailable", "NotAllowedError"));
                return;
            }
            window.webauthnBridge.getAssertion(rpId, challengeB64, function(resJson) {
                let res = JSON.parse(resJson);
                if (!res.success) {
                    reject(new DOMException(res.error || "User cancelled", "NotAllowedError"));
                    return;
                }
                let cred = {
                    id: res.id,
                    rawId: b64ToBuf(res.rawId_b64),
                    type: 'public-key',
                    response: {
                        clientDataJSON: b64ToBuf(res.clientDataJSON_b64),
                        authenticatorData: b64ToBuf(res.authenticatorData_b64),
                        signature: b64ToBuf(res.signature_b64),
                        userHandle: res.userHandle_b64 ? b64ToBuf(res.userHandle_b64) : null
                    },
                    getClientExtensionResults: () => ({})
                };
                resolve(cred);
            });
        });
    };
    console.log("[Theonix] Native WebAuthn Passkey Bridge active on " + window.location.hostname);
})();
"""


class TheonixWebPage(QWebEnginePage if HAS_WEBENGINE else object):
    """Custom WebEngine Page with permission routing and window creation handling."""
    new_tab_requested = pyqtSignal(QUrl)

    def __init__(self, profile=None, parent=None):
        if HAS_WEBENGINE:
            super().__init__(profile, parent)
            self.featurePermissionRequested.connect(self._on_permission_requested)

    def _on_permission_requested(self, security_origin: QUrl, feature):
        self.setFeaturePermission(security_origin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

    def createWindow(self, window_type):
        self.new_tab_requested.emit(QUrl())
        return None


class TheonixWebView(QWebEngineView if HAS_WEBENGINE else QWidget):
    """Main Web View component with Chromium rendering, Passkey bridge, and THAID extraction."""
    title_updated = pyqtSignal(str)
    url_updated = pyqtSignal(QUrl)
    load_progress_changed = pyqtSignal(int)
    new_window_requested = pyqtSignal(QUrl)

    def __init__(self, profile: 'QWebEngineProfile' = None, parent=None):
        if HAS_WEBENGINE:
            super().__init__(parent)
            self.custom_page = TheonixWebPage(profile or QWebEngineProfile.defaultProfile(), self)
            self.setPage(self.custom_page)

            # WebAuthn QWebChannel setup
            self.channel = QWebChannel(self.page())
            self.webauthn_bridge = WebAuthnBridge(self)
            self.channel.registerObject("webauthnBridge", self.webauthn_bridge)
            self.page().setWebChannel(self.channel)

            # Connect core WebEngine signals
            self.titleChanged.connect(self.title_updated)
            self.urlChanged.connect(self.url_updated)
            self.loadProgress.connect(self.load_progress_changed)
            self.loadFinished.connect(self._on_load_finished)
            self.custom_page.new_tab_requested.connect(self.new_window_requested)

            # Configure high-performance Chromium settings
            settings = self.settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        else:
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.browser = QTextBrowser()
            self.browser.setOpenExternalLinks(True)
            self.browser.setStyleSheet("background-color: #07090E; border: none; color: #F8FAFC; padding: 20px;")
            layout.addWidget(self.browser)
            self._current_url = QUrl("https://duckduckgo.com")

    def _on_load_finished(self, ok: bool):
        if ok and HAS_WEBENGINE:
            qwebchannel_code = get_qwebchannel_js()
            init_js = f"""
            (function() {{
                {qwebchannel_code}
                if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {{
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        window.webauthnBridge = channel.objects.webauthnBridge;
                        {WEBAUTHN_INJECTION_JS}
                    }});
                }}
            }})();
            """
            self.page().runJavaScript(init_js)

    def load_url(self, url: QUrl):
        if HAS_WEBENGINE:
            self.load(url)
        else:
            self._current_url = url
            from .new_tab_page import get_new_tab_html
            url_str = url.toString()
            if url_str == "theonix://newtab":
                html = get_new_tab_html()
            else:
                domain = url.host() or url_str
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            background-color: #07090E;
                            color: #F8FAFC;
                            font-family: 'Segoe UI', system-ui, sans-serif;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                        }}
                        .card {{
                            background: rgba(16, 22, 34, 0.85);
                            border: 1px solid #1E2638;
                            border-radius: 16px;
                            padding: 32px;
                            max-width: 500px;
                            text-align: center;
                        }}
                        h2 {{ color: #00FFAA; margin: 0 0 12px 0; }}
                        .url-text {{ color: #00D4FF; word-break: break-all; }}
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div style="font-size: 28px; margin-bottom: 12px;">🌐</div>
                        <h2>Navigating to <span class="url-text">{domain}</span></h2>
                        <p style="color: #94A3B8; font-size: 14px; margin-top: 8px; line-height: 1.6;">
                            Resource URL: <a href="{url_str}" style="color: #00D4FF;">{url_str}</a>
                        </p>
                    </div>
                </body>
                </html>
                """
            self.browser.setHtml(html)
            self.url_updated.emit(url)
            self.title_updated.emit(url.host() or "New Tab")
            self.load_progress_changed.emit(100)

    def current_url(self) -> QUrl:
        if HAS_WEBENGINE:
            return self.url()
        return self._current_url

    def extract_page_text(self, callback: Callable[[str], None]):
        if not HAS_WEBENGINE:
            callback(self.browser.toPlainText() if hasattr(self, "browser") else "")
            return

        js_script = """
        (function() {
            let article = document.querySelector('article') || document.querySelector('main') || document.body;
            let text = article ? article.innerText : document.body.innerText;
            return text.substring(0, 8000);
        })();
        """
        self.page().runJavaScript(js_script, callback)

    def extract_selected_text(self, callback: Callable[[str], None]):
        if not HAS_WEBENGINE:
            callback("")
            return

        js_script = "window.getSelection().toString();"
        self.page().runJavaScript(js_script, callback)

    def zoom_in(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(min(3.0, self.zoomFactor() + 0.1))

    def zoom_out(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(max(0.25, self.zoomFactor() - 0.1))

    def reset_zoom(self):
        if HAS_WEBENGINE:
            self.setZoomFactor(1.0)
