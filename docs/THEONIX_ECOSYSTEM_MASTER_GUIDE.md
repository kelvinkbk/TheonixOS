# 🌐 Theonix OS — Master Ecosystem & Application Architecture Guide

> **Official Comprehensive Architecture Document for LLMs, AI Engineers & Developers**  
> *Target System: Theonix OS (Arch Linux + KDE/KWin + Cyber-Obsidian Design System)*  
> *Repository: `kelvinkbk/TheonixOS`*

---

## 🏛️ 1. Operating System Architecture Overview

**Theonix OS** is a next-generation Linux desktop operating system featuring an integrated native ecosystem. All applications, core daemons, and system layers share a unified **Cyber-Obsidian Glassmorphism** design language, communicate via **D-Bus session buses**, and leverage local-first AI and cryptographic security.

```text
                               THEONIX OS ECOSYSTEM
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
   🖥️ GUI APPLICATIONS          ⚡ SYSTEM SERVICES              🛡️ CORE & SECURITY
        │                               │                               │
   ├─ THAID AI Assistant           ├─ Update Service (D-Bus)       ├─ theonix-core (SDK)
   ├─ Theonix Store                ├─ Auth & Passkey Service       ├─ UACL (Access Control)
   ├─ Theonix Browser              ├─ Notification Service         ├─ App Manager
   ├─ Theonix Files                ├─ Search Service (Spotlight)   └─ Calamares / Live ISO
   ├─ Theonix Messages             └─ Input Gesture Service
   ├─ Theonix Settings
   └─ Theonix Welcome / Wizard
```

---

## 🎨 2. UI/UX & Design Tokens (Theonix Theme System)

All Theonix native applications are built using **PyQt6** and adhere to the **Cyber-Obsidian** design language:

| Design Token | Hex / Value | Usage |
| :--- | :--- | :--- |
| **Dark Base (Void)** | `#050814` / `#07090E` | Main window backgrounds |
| **Surface Glass** | `#0B0E17` / `rgba(16, 22, 34, 0.85)` | Cards, panels, sidebar backgrounds |
| **Accent Primary (Neon Cyan)** | `#00FFAA` / `#00D4FF` | Active indicators, highlights, CTAs |
| **Accent AI / Crypto (Purple)** | `#A855F7` / `#C084FC` | THAID AI elements, Passkey security modals |
| **Danger / Destructive** | `#EF4444` / `#F87171` | Remove buttons, warnings, error states |
| **Glass Border** | `1px solid rgba(255, 255, 255, 0.08)` | Translucent borders across all cards |
| **Typography** | `Inter`, `Segoe UI`, system sans-serif | Modern, crisp UI font hierarchy |

---

## 📱 3. Native GUI Applications Directory

---

### 3.1 🤖 THAID AI Assistant
* **Binary / Launcher**: `thaid-gui`, `Super+Space`
* **Directory**: `/home/k/Desktop/Projects/theonix/thaid-gui` & `/home/k/Desktop/Projects/theonix/thaid`
* **Technology**: PyQt6, Local LLM backend (Ollama / Llama.cpp), Piper TTS, Vosk/Whisper STT
* **Key Capabilities**:
  * **Floating AI Orb**: Draggable, translucent desktop overlay widget with glowing visualizer.
  * **Hands-free Wake Word**: Detects `"Hey Theonix"` in the background with zero cloud telemetry.
  * **Neural Voice Synthesis**: Natural local speech response using Piper neural models.
  * **OS Automation & Routing**: Reads screen context, launches apps, runs system queries, and controls settings.
  * **Destructive Action Safety**: Prompts for user authorization via `org.theonix.Auth` before executing dangerous bash/root tasks.

---

### 3.2 🛍️ Theonix Store
* **Binary / Launcher**: `theonix-store`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-store`
* **Technology**: PyQt6, Pacman / ALPM, Flatpak API, AppImage runtime
* **Key Capabilities**:
  * **Unified Software Center**: Installs and updates Arch Native (`.pkg.tar.zst`), Flatpak (`Flathub`), and AppImages.
  * **Curated Channels**: Featured apps, AI developer tools, gaming, productivity, and system utilities.
  * **One-Click Sandbox Installation**: Automated dependency resolution and UACL permission granting.
  * **Cyber-Obsidian Storefront**: Glass cards, banner carousels, screenshots gallery, and changelog viewer.

---

### 3.3 🌐 Theonix Browser
* **Binary / Launcher**: `theonix-browser [url]`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-browser`
* **Technology**: PyQt6, QtWebEngine (Chromium Core), QWebChannel, WebAuthn Passkey Bridge
* **Key Capabilities**:
  * **Native WebAuthn / FIDO2 Passkey Bridge**: Intercepts `navigator.credentials.create()` and `navigator.credentials.get()` in JavaScript, converting WebAuthn calls into local `org.theonix.Auth` SECP256R1 cryptographic signatures without requiring physical USB hardware.
  * **THAID Web Companion**: 1-click **Ask Theonix** button that extracts readable DOM text and feeds it to THAID for instant summaries, translations, and research notes.
  * **High-Performance Chromium Settings**: Hardware acceleration, WebGL/WebGPU, dark mode auto-injection, tab suspension.

---

### 3.4 📁 Theonix Files
* **Binary / Launcher**: `theonix-files [path]`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-files`
* **Technology**: PyQt6, KIO / GLib Gio, SQLite
* **Key Capabilities**:
  * **Cyber-Obsidian File Browser**: Split-view, tree navigation, breadcrumb path bar, and thumbnail previews.
  * **AI Tagging & Smart Folders**: Local natural language file search integrated with `org.theonix.Search`.
  * **Integrated Terminal Drawer**: Built-in dropdown terminal synced to current working directory.

---

### 3.5 💬 Theonix Messages
* **Binary / Launcher**: `theonix-messages`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-messages`
* **Technology**: PyQt6, Matrix Protocol (Matrix-NIO), E2EE Olm/Megolm
* **Key Capabilities**:
  * **Decentralized Chat Hub**: Native Matrix communication for direct messages, developer spaces, and community rooms.
  * **AI Smart Replies**: THAID suggests contextual message replies directly inline.
  * **Obsidian Glass Chat Interface**: Translucent message bubbles, voice note player, markdown rendering.

---

### 3.6 ⚙️ Theonix Settings
* **Binary / Launcher**: `theonix-settings`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-settings`
* **Technology**: PyQt6, D-Bus system/session integration, SQLite
* **Navigation Modules**:
  1. `System · About`: Hardware specs, kernel version, Theonix build number, uptime.
  2. `AI · THAID`: Local LLM model switching, wake-word sensitivity, neural voice selection.
  3. `Appearance`: Dark/Light Cyber themes, accent color pickers, wallpaper manager.
  4. `Display · Scaling`: Resolution switching, multi-monitor arrangement, fractional scaling (100%, 125%, 150%, 200%).
  5. `Touchpad · Gestures`: 1/2/3/4 finger gesture configuration via `org.theonix.Input`.
  6. `Voice Assistant`: Microphone input levels, Piper audio testing, offline speech engine.
  7. `Network · Wi-Fi`: NetworkManager backend, QR code connection sharing.
  8. `Sound · Audio`: PipeWire audio routing, device switching, volume booster.
  9. `Storage · Snapshots`: Btrfs snapshot management, disk usage visualization.
  10. `Advanced · Developer`: Developer mode logs, UACL execution trace, **🔑 Passkeys & FIDO2 Security Vault** (live hardware token detection, list passkeys, register/remove passkeys).
  11. `System Updates`: Background update orchestration via `org.theonix.Updates`.

---

### 3.7 🧙 Theonix Welcome / Setup Wizard
* **Binary / Launcher**: `theonix-wizard`
* **Directory**: `/home/k/Desktop/Projects/theonix/theonix-wizard`
* **Technology**: PyQt6, PyYAML, Systemd integration
* **Key Capabilities**:
  * **First-Run Onboarding**: Walkthrough for new users to pick theme presets, download AI models, configure graphics drivers (NVIDIA / AMD / Intel), and set up account passkeys.

---

## ⚡ 4. Decoupled Core D-Bus System Services

Theonix OS runs 5 decoupled background daemons configured as persistent systemd user services (`~/.config/systemd/user/`):

```text
┌────────────────────────────────┬───────────────────────────┬──────────────────────────────────────────┐
│ Service Name                   │ D-Bus Well-Known Name     │ Object Path                              │
├────────────────────────────────┼───────────────────────────┼──────────────────────────────────────────┤
│ theonix-updates.service        │ org.theonix.Updates       │ /org/theonix/Updates                     │
│ theonix-auth.service           │ org.theonix.Auth          │ /org/theonix/Auth                        │
│ theonix-notifications.service  │ org.theonix.Notifications │ /org/theonix/Notifications               │
│ theonix-search.service         │ org.theonix.Search        │ /org/theonix/Search                      │
│ theonix-input.service          │ org.theonix.Input         │ /org/theonix/Input                       │
└────────────────────────────────┴───────────────────────────┴──────────────────────────────────────────┘
```

---

### 4.1 🔄 `theonix-update-service` (`org.theonix.Updates`)
* **File**: `services/update_service.py`
* **D-Bus Interface Methods**:
  * `CheckUpdates() -> str`: Scans Pacman mirrors and Flathub asynchronously; returns JSON `{ "pacman_updates": [...], "flatpak_updates": [...], "count": N }`.
  * `ApplyUpdates(types: str) -> bool`: Orchestrates safe update downloads with progress signals.
  * `GetSystemStatus() -> str`: Telemetry data on OS version, kernel, uptime, and last update timestamp.
* **Signals**: `updateProgress(int percent, str message)`, `updatesAvailable(int count)`.

---

### 4.2 🔐 `theonix-auth-service` (`org.theonix.Auth`)
* **File**: `services/auth_service.py`
* **Database Vault**: SQLite at `~/.config/theonix/auth_vault.db`
* **Cryptographic Engine**: `ECDSA SECP256R1 (P-256)` with SHA-256 signatures, WebAuthn/FIDO2 standard clientDataJSON and CBOR AttestationObject structures.
* **D-Bus Interface Methods**:
  * `CreatePasskey(rp_id: str, user_name: str, user_display_name: str) -> str`: Displays glowing `GlassPasskeyDialog` modal; generates ECDSA keypair; returns credential JSON.
  * `AuthenticatePasskey(rp_id: str, challenge: str) -> str`: Displays modal with **Account Selector Dropdown**; signs `authData + SHA256(clientDataJSON)`; returns assertion signature.
  * `ListPasskeys() -> str`: Returns all stored passkeys with usage counters and timestamps.
  * `DeletePasskey(passkey_id: str) -> bool`: Removes credential from vault.
  * `DetectAuthenticators() -> str`: Scans USB HID subsystem for connected hardware security keys (Yubico, Google Titan, Nitrokey, Feitian, SoloKeys, Canokey) and local platform vault status.
  * `VerifyPassword(password: str) -> bool`: Validates user credentials against Linux PAM authentication.
  * `RequestAuthorization(app_name: str, action: str, target: str, risk_level: str) -> bool`: Prompts user before THAID executes privileged or destructive actions.

---

### 4.3 🔔 `theonix-notification-service` (`org.theonix.Notifications`)
* **File**: `services/notification_service.py`
* **D-Bus Interface Methods**:
  * `Notify(title: str, message: str, icon: str, urgency: str, actions_json: str) -> int`: Spawns a floating translucent Cyber-Obsidian banner at the top-right of the screen with optional interactive action buttons.
  * `CloseNotification(nid: int) -> bool`: Dismisses active banner.
* **Signals**: `ActionInvoked(int nid, str action_key)`, `NotificationClosed(int nid)`.

---

### 4.4 🗃️ `theonix-search-service` (`org.theonix.Search`)
* **File**: `services/search_service.py`
* **Spotlight Launcher**: `Super+Space` / `theonix-search`
* **D-Bus Interface Methods**:
  * `Search(query: str) -> str`: Omni-search indexer querying Desktop Apps (`/usr/share/applications`), Files, Settings pages, and System Commands.
  * `ToggleSpotlight() -> bool`: Toggles the centered translucent macOS/Spotlight-style floating search bar.
  * `Reindex() -> bool`: Rebuilds the search cache.

---

### 4.5 🖐️ `theonix-input-service` (`org.theonix.Input`)
* **File**: `services/input_service.py`
* **D-Bus Interface Methods**:
  * `GetGestureSettings() -> str`: Returns configured 1/2/3/4 finger actions (Swipe Left/Right = Switch Virtual Desktop, Pinch = Zoom, 3-Finger Tap = Open Search).
  * `SetGestureAction(gesture_id: str, action: str) -> bool`: Updates gesture bindings and synchronizes with KWin compositor.
  * `TriggerAction(action: str) -> bool`: Executes window management or compositor actions immediately.

---

## 🧰 5. Theonix Core SDK (`theonix-core`)

All Theonix Python applications import the unified SDK from `/home/k/Desktop/Projects/theonix/theonix-core`:

```python
from theonix_core import (
    # D-Bus Client Classes
    UpdateClient,          # UpdateClient.check_updates(), get_system_status()
    AuthClient,            # AuthClient.create_passkey(), authenticate_passkey(), detect_authenticators()
    NotificationClient,    # NotificationClient.notify("Title", "Message", urgency="normal")
    SearchClient,          # SearchClient.search("query"), toggle_spotlight()
    InputClient,           # InputClient.get_gesture_settings()
    
    # Core Engine Classes
    VoiceEngine,           # Local TTS / STT audio engine
    AppManager,            # App lifecycle and process supervisor
    UACL,                  # Security permission gating
    
    # UI Components & Themes
    apply_theonix_style,   # Sets global Cyber-Obsidian QSS stylesheet
    GlassCard,             # Translucent container widget with rounded borders
    NavButton,             # Sidebar navigation button with neon pill indicator
    Badge                  # Status pill label
)
```

---

## 📦 6. Packaging, Build & Deployment (Arch Linux PKGBUILDs)

The repository provides official Arch Linux PKGBUILDs located in `/home/k/Desktop/Projects/theonix/packages/`:

* `packages/theonix-core/PKGBUILD`: Builds and installs `python-theonix-core` into `/usr/lib/python3.*/site-packages/theonix_core/` and systemd unit files into `/usr/lib/systemd/user/`.
* `packages/theonix-settings/PKGBUILD`: Installs Theonix Settings binary to `/usr/bin/theonix-settings` and desktop entry to `/usr/share/applications/theonix-settings.desktop`.
* `packages/theonix-store/PKGBUILD`: Builds native Theonix Store binary and desktop assets.
* `profile/`: Archiso build definitions, live filesystem rootfs (`airootfs`), kernel hooks, and Plymouth/KDE splash configuration.

---

## 🚀 7. Key Developer Cheatsheet & Test Commands

```bash
# 1. Test all 5 Core Services & Passkey Vault
python3 /home/k/Desktop/Projects/theonix/scripts/test_services.py

# 2. Launch Theonix Native Apps
theonix-settings
theonix-browser https://passkeys.io
theonix-store
thaid-gui

# 3. Passkey Vault Operations (Python SDK)
python3 -c "
from theonix_core import AuthClient
print('Stored Passkeys:', AuthClient.list_passkeys())
print('Authenticators:', AuthClient.detect_authenticators())
"

# 4. Restart Background Daemons
systemctl --user restart theonix-auth.service
systemctl --user restart theonix-updates.service
systemctl --user restart theonix-notifications.service
systemctl --user restart theonix-search.service
systemctl --user restart theonix-input.service
```
