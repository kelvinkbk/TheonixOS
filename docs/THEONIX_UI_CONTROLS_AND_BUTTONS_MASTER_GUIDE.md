# 🎛️ Theonix OS — Complete UI Controls, Buttons & Components Master Guide

> **Granular Screen-by-Screen & Button-by-Button UI Guide for ChatGPT, AI Agents & Developers**  
> *Target System: Theonix OS (PyQt6 Cyber-Obsidian UI System)*  
> *Repository: `kelvinkbk/TheonixOS`*

---

## 🏛️ UI Design System Overview

All Theonix OS applications are built on **PyQt6** using the **Cyber-Obsidian** translucent glass styling (`theonix-core/theonix_core/ui.py`).

### Standard Reusable Component Types:
* **`GlassCard`**: Translucent container card (`rgba(16, 22, 34, 0.85)`) with rounded corners (`16px`) and subtle borders (`rgba(255, 255, 255, 0.08)`).
* **`NavButton`**: Sidebar navigation button with cyber hover glow and active neon indicator strip.
* **`ActionBtn`**: Primary CTA button with gradient fill (`#00FFAA` ➔ `#00D4FF` or `#A855F7` ➔ `#6366F1`).
* **`DangerBtn`**: Red translucent button for destructive actions (`#EF4444`).
* **`Badge`**: Status indicator pill (e.g. `Active`, `Listening`, `Ready`).

---

## 1. ⚙️ Theonix Settings (`theonix-settings`)

* **Launcher**: `theonix-settings`
* **Source**: `theonix-settings/main.py`
* **Layout**: Left Navigation Sidebar + Right Dynamic Content Stack (`QStackedWidget`).

### 1.0 Sidebar Navigation Controls
* **Search Input (`QLineEdit`)**: `"Search settings..."` — Real-time filter across all 11 settings pages.
* **Navigation Buttons (`NavButton`)**:
  1. `System · About` (Index 0)
  2. `AI · THAID` (Index 1)
  3. `Appearance` (Index 2)
  4. `Display · Scaling` (Index 3)
  5. `Touchpad · Gestures` (Index 4)
  6. `Voice Assistant` (Index 5)
  7. `Network · Wi-Fi` (Index 6)
  8. `Sound · Audio` (Index 7)
  9. `Storage · Snapshots` (Index 8)
  10. `Advanced · Developer` (Index 9)
  11. `System Updates` (Index 10)

---

### 1.1 Page: `System · About` (`SystemAboutPage`)
* **Hardware & OS Specs Card**:
  * Displays: OS Name (`Theonix OS 1.0`), Kernel (`Linux 6.x-arch`), CPU Model, Memory RAM Usage, Hostname, Uptime.
  * `[Copy System Info]` Button: Copies formatted system diagnostics to clipboard.
* **System Actions Card**:
  * `[Check System Health]` Button: Runs local diagnostic scripts.
  * `[System Logs]` Button: Launches journalctl log viewer.

---

### 1.2 Page: `AI · THAID` (`AISettingsPage`)
* **Local LLM Model Selection Card**:
  * **Model Dropdown (`QComboBox`)**: Options: `Llama 3 8B (Recommended)`, `Mistral 7B`, `Phi-3 Mini`, `Custom Local Ollama Model`.
  * **Context Length Slider (`QSlider`)**: Range: `2048` to `16384` tokens.
  * `[Download / Manage Models]` Button: Opens Ollama model repository manager.
* **Voice & Personality Card**:
  * **Voice Selector (`QComboBox`)**: Options: `Theonix Neural (Piper)`, `En-US Calm`, `En-GB Crisp`.
  * `[Test Voice Synthesis]` Button: Synthesizes sample speech output via `VoiceEngine`.
* **Automation & Privacy Card**:
  * **Wake Word Toggle (`QCheckBox`)**: `"Enable hands-free 'Hey Theonix' wake word detection"`.
  * **Screen Context Toggle (`QCheckBox`)**: `"Allow THAID to inspect active window for context"`.
  * **Permission Level Dropdown (`QComboBox`)**: `Strict Prompting (UACL)`, `Balanced`, `Developer Auto-Confirm`.

---

### 1.3 Page: `Appearance` (`AppearancePage`)
* **Theme Presets Card**:
  * `[Cyber Obsidian (Default)]` Card Button: Deep void dark mode with neon cyan highlights.
  * `[Void Purple]` Card Button: Neon violet and indigo theme.
  * `[Solaris Light]` Card Button: High-contrast translucent light theme.
* **Accent Color Selector**:
  * Interactive color chips: `Neon Cyan (#00FFAA)`, `Electric Blue (#38BDF8)`, `Cyber Purple (#A855F7)`, `Emerald Green (#10B981)`.
* **Wallpaper Manager Card**:
  * Wallpaper Grid: 6 built-in Cyber-Obsidian wallpaper thumbnails.
  * `[Custom Wallpaper (+)]` Button: Opens `QFileDialog` to select custom PNG/JPG.
* **Window Transparency Slider (`QSlider`)**: Adjusts desktop blur and glass opacity (70% - 100%).

---

### 1.4 Page: `Display · Scaling` (`DisplayPage`)
* **Resolution & Refresh Rate Card**:
  * **Resolution Dropdown (`QComboBox`)**: `3840x2160 (4K)`, `2560x1440 (2K)`, `1920x1080 (FHD)`.
  * **Refresh Rate Dropdown (`QComboBox`)**: `60 Hz`, `120 Hz`, `144 Hz`, `165 Hz`, `240 Hz`.
* **Display Scaling Buttons (Fractional Scaling)**:
  * `[100% (Native)]` Toggle Button
  * `[125%]` Toggle Button
  * `[150% (Recommended for 2K/4K)]` Toggle Button
  * `[200%]` Toggle Button
* **Multi-Monitor Arrangement**:
  * Drag-and-drop monitor layout canvas.
  * `[Identify Displays]` Button: Numbers monitors on screen.
  * `[Apply Display Settings]` Action Button: Syncs via KWin/Wayland.

---

### 1.5 Page: `Touchpad · Gestures` (`TouchpadGesturesPage`)
* **Hardware Status Banner (`Badge`)**: Shows detected touchpad device (`libinput`).
* **Multi-Finger Gesture Bindings**:
  * **3-Finger Swipe Left / Right (`QComboBox`)**: Options: `Switch Virtual Desktop`, `Cycle Windows`, `None`.
  * **3-Finger Swipe Up (`QComboBox`)**: Options: `Toggle Overview / Task View`, `Maximize Window`.
  * **3-Finger Swipe Down (`QComboBox`)**: Options: `Show Desktop`, `Minimize Window`.
  * **3-Finger Tap (`QComboBox`)**: Options: `Open Omni-Search Spotlight (Super+Space)`, `Middle Click`.
  * **4-Finger Swipe Left / Right (`QComboBox`)**: Options: `Switch Workspaces`, `Next/Previous Tab`.
  * **Pinch-to-Zoom Toggle (`QCheckBox`)**: `"Enable fluid smooth pinch zooming"`.
* **Touchpad Speed Sliders**:
  * **Pointer Speed Slider (`QSlider`)**: Adjusts cursor acceleration.
  * **Natural Scrolling Toggle (`QCheckBox`)**: Inverts scroll direction.
* `[Save & Apply Gestures]` Action Button: Calls `org.theonix.Input.SetGestureAction()`.

---

### 1.6 Page: `Voice Assistant` (`VoiceAssistantPage`)
* **Microphone Input Card**:
  * **Audio Input Device (`QComboBox`)**: Lists PulseAudio/PipeWire microphones.
  * **Microphone Level Meter (`QProgressBar`)**: Live audio amplitude visualizer.
  * **Sensitivity Slider (`QSlider`)**: Adjusts background noise gate.
* **Offline Speech-to-Text (STT) Engine Card**:
  * **Model Dropdown (`QComboBox`)**: `Vosk Lightweight (Offline)`, `Whisper Tiny`, `Whisper Base`.
  * `[Download STT Model]` Button.
* **Voice Trigger Audio Chime Toggle (`QCheckBox`)**: Plays sound when THAID activates.

---

### 1.7 Page: `Network · Wi-Fi` (`NetworkPage`)
* **Wi-Fi Hardware Card**:
  * **Wi-Fi Power Toggle (`QPushButton`)**: `[Turn Wi-Fi Off]` / `[Turn Wi-Fi On]`.
  * `[Scan Networks]` Button: Refreshes visible SSIDs.
* **Available Networks List (`QTableWidget`)**:
  * Columns: `Network SSID`, `Security (WPA2/WPA3)`, `Signal Strength`, `Action`.
  * `[Connect]` Button per row: Opens password prompt dialog.
  * `[Disconnect]` Button for active network.
* **Hotspot & Sharing Card**:
  * `[Create Wi-Fi Hotspot]` Button.
  * `[Show QR Code]` Button: Displays QR code for mobile devices.

---

### 1.8 Page: `Sound · Audio` (`AudioPage`)
* **Output Device Card**:
  * **Speaker / Headphone Selector (`QComboBox`)**: PipeWire audio sinks.
  * **Master Volume Slider (`QSlider`)**: 0% to 150% (over-amplification support).
  * `[Test Sound]` Button: Plays left/right channel chime.
* **Input Device Card**:
  * **Microphone Selector (`QComboBox`)**: PipeWire source devices.
  * **Input Gain Slider (`QSlider`)**.
* **Application Volume Mixer**:
  * Lists per-app volume sliders for active apps (Browser, Spotify, Games).

---

### 1.9 Page: `Storage · Snapshots` (`StoragePage`)
* **Disk Usage Breakdown**:
  * Visual progress bar: Root `/`, Home `/home`, Swap.
  * `[Clean Cache / Junk]` Button: Clears pacman cache and temp files.
* **Btrfs Snapshot Management Card**:
  * `[+ Create Snapshot Now]` Action Button: Generates instant read-only system restore point.
  * **Snapshot History Table (`QTableWidget`)**:
    * Columns: `Snapshot ID`, `Date / Timestamp`, `Description`, `Action`.
    * `[Restore]` Button: Reverts system state to snapshot.
    * `[Delete]` Button: Frees snapshot disk space.

---

### 1.10 Page: `Advanced · Developer` (`AdvancedPage`)
* **Developer Environment Card**:
  * **Debug Logs Toggle (`QCheckBox`)**: `"Enable Theonix Developer Mode & Debug Logs"`.
  * **UACL Trace Toggle (`QCheckBox`)**: `"Enable UACL Execution Trace & Proton Diagnostics"`.
  * `[Open Terminal]` Button: Launches Alacritty/Konsole.
  * `[Recovery Tools]` Button: Opens GRUB and EFI boot manager.
* **🔑 Passkeys & FIDO2 Security Vault Card**:
  * **Live Detection Banner (`QLabel`)**:
    * Green: `🟢 Platform Authenticator: Active (ECDSA P-256) | 🔑 USB Security Keys: [Detected Name]`
    * Blue: `🟢 Platform Authenticator: Active (ECDSA P-256) | 🔑 USB Security Keys: Listening...`
  * **Passkey Vault Table (`QTableWidget`)**:
    * Columns: `Website / Domain` (e.g. `🔑 passkeys.io`), `Account / Username` (e.g. `kelvinkbkk@gmail.com`), `Action`.
    * `[Remove]` Button (Red Glass): Instantly deletes passkey from `auth_vault.db`.
  * **Vault Control Buttons**:
    * `[+ Register New Passkey]` Action Button: Prompts `GlassPasskeyDialog` for manual passkey generation.
    * `[Scan Authenticators]` Action Button: Refreshes real-time USB FIDO2 tokens via `org.theonix.Auth.DetectAuthenticators()`.

---

### 1.11 Page: `System Updates` (`UpdatesPage`)
* **Update Engine Status Card**:
  * Displays: Last check timestamp, active package channel (`Arch Stable + Flathub`).
  * `[Check for Updates]` Action Button: Calls `org.theonix.Updates.CheckUpdates()`.
* **Pending Packages List (`QTableWidget`)**:
  * Columns: `Package Name`, `Current Version`, `New Version`, `Repository`.
* **Update Progress (`QProgressBar`)**: Shows live download and installation percentage.
* `[Install All Updates]` Action Button: Executes transactional system update.

---

## 2. 🤖 THAID AI Assistant (`thaid-gui`)

* **Launcher**: `thaid-gui`, `Super+Space`
* **Source**: `thaid-gui/main.py`, `thaid/`

### 2.1 Floating Desktop Orb (Widget)
* **Draggable Translucent Orb**: Click to expand THAID drawer; double click to toggle voice listening.
* **Audio Wave Visualizer**: Glows neon purple/cyan during listening and speaking states.

### 2.2 Main Assistant Window Controls
* **Header Bar**:
  * **Model Selector (`QComboBox`)**: Switches active local LLM (`Llama 3`, `Mistral`, `DeepSeek-Coder`).
  * `[📌 Pin Window]` Button: Keeps THAID always on top.
  * `[🗑️ Clear Conversation]` Button: Resets memory and starts new context session.
  * `[✕ Close]` Button: Minimizes back to floating orb.
* **Conversation History Stream (`QScrollArea`)**:
  * User Message bubble (Obsidian blue glass).
  * THAID Response bubble (Markdown rendered, code highlighting with `[Copy Code]` buttons).
* **Bottom Command Bar**:
  * **Prompt Text Input (`QTextEdit`)**: Multi-line input with auto-expanding height (`Shift+Enter` = newline, `Enter` = send).
  * `[📎 Attach File / Image]` Button: Attaches document or screenshot for vision/analysis.
  * `[🎙️ Voice Mode]` Toggle Button: Starts real-time hands-free conversation.
  * `[➤ Send]` Action Button: Dispatches prompt to local LLM backend.

### 2.3 Destructive Action Modal (`GlassAuthDialog`)
* **Header**: `🛡️ Authorization Requested`
* **Details**: App Name, requested command/action (e.g. `rm -rf`, `systemctl restart`), Risk Level.
* **Password/PIN Input (`QLineEdit`)**: Optional user account password verification.
* `[Deny]` Button: Cancels execution.
* `[Authorize]` Button: Approves execution and resumes THAID task.

---

## 3. 🛍️ Theonix Store (`theonix-store`)

* **Launcher**: `theonix-store`
* **Source**: `theonix-store/main.py`

### 3.1 Top Navigation Bar
* **Search Input (`QLineEdit`)**: `"Search thousands of apps, flatpaks, and games..."`
* **Category Filter Pills (`QPushButton`)**:
  * `[🔥 Featured]`, `[🤖 AI & ML]`, `[💻 Development]`, `[🎮 Gaming]`, `[🎨 Creative]`, `[⚡ System]`.
* **Package Source Switcher (`QComboBox`)**:
  * `All Sources`, `Arch Native (.pkg)`, `Flatpak (Flathub)`, `AppImage`.
* `[🔄 Updates Tab]` Button: Shows badge with available app updates.

### 3.2 App Card Controls (Storefront Grid)
* **App Icon & Title**: Click opens detailed modal.
* **Package Type Badge**: `Native`, `Flatpak`, `AppImage`.
* **Action Buttons per App**:
  * `[Install]` (Neon Cyan Button): Downloads and installs package in background.
  * `[Launch]` (Electric Blue Button): Executes installed binary.
  * `[Remove]` (Red Glass Button): Uninstalls package.
  * `[Update]` (Purple Button): Updates specific application.

### 3.3 App Detail Modal
* Screenshots carousel with next/prev buttons.
* Description, permissions required (Camera, Network, Filesystem).
* Source repository link, developer website, license.
* `[Install Version X.Y.Z]` CTA Button.

---

## 4. 🌐 Theonix Browser (`theonix-browser`)

* **Launcher**: `theonix-browser [url]`
* **Source**: `theonix-browser/main.py`, `app/`

### 4.1 Top Window Toolbar
* **Navigation Controls**:
  * `[◀ Back]` Button (`browser.back()`)
  * `[▶ Forward]` Button (`browser.forward()`)
  * `[↻ Reload]` Button (`browser.reload()`)
  * `[⌂ Home]` Button (`browser.load_url("theonix://newtab")`)
* **Unified Omnibox / URL Bar (`QLineEdit`)**:
  * Displays current URL / Search query with SSL padlock indicator (`🔒`).
  * Autocomplete suggestions for bookmarks, history, and search engine.
* **Toolbar Utility Buttons**:
  * `[★ Bookmark Star]` Button: Adds current URL to bookmarks with folder picker.
  * `[✨ Ask Theonix]` Action Button (Purple Gradient): Extracts visible page DOM text and launches THAID AI sidebar to summarize/analyze the page.
  * `[📥 Downloads]` Button: Opens floating downloads manager.
  * `[📜 History]` Button: Opens history viewer modal.
  * `[⚙️ Browser Settings]` Button: Configures search engine, privacy shields, hardware acceleration.

### 4.2 Tab Bar
* Individual Tabs with Favicon, Page Title, and `[✕ Close Tab]` button.
* `[+ New Tab]` Button.

### 4.3 🔑 Native Passkey Modal (`GlassPasskeyDialog`)
* **Header**: `🔑 Sign in with Passkey` / `Create Passkey`
* **Website Label**: `Website / App: domain.com`
* **Account Selector (`QComboBox`)**: Lists all registered accounts (e.g. `👤 kelvinkbkk@gmail.com`) for multi-account login.
* **Password/PIN Input (`QLineEdit`)**: Optional password fallback.
* `[Cancel]` Button: Cancels WebAuthn request.
* `[Use Passkey]` / `[Save Passkey]` (Purple Gradient Button): Generates ECDSA P-256 signature and completes login.

---

## 5. 📁 Theonix Files (`theonix-files`)

* **Launcher**: `theonix-files [path]`
* **Source**: `theonix-files/main.py`

### 5.1 Main Toolbar
* **Navigation Buttons**: `[◀ Back]`, `[▶ Forward]`, `[▲ Up Directory]`.
* **Path Breadcrumb Bar**: Clickable path segments (`Home ➔ Desktop ➔ Projects`).
* **Search Bar (`QLineEdit`)**: Instant file search with fuzzy matching.
* **Action Buttons**:
  * `[+ New Folder]` Button: Prompts for folder name.
  * `[>_ Terminal]` Toggle Button: Drops down embedded terminal drawer.
  * `[⊞ Grid / ☰ List]` View Mode Toggle Button.

### 5.2 Sidebar Places Navigation
* `🏠 Home`, `🖥️ Desktop`, `📁 Documents`, `📥 Downloads`, `🎵 Music`, `🖼️ Pictures`, `🎬 Videos`, `🗑️ Trash`.
* **Drives / Mounts Section**: Lists internal NVMe/SSDs and external USB flash drives with `[⏏ Unmount]` buttons.

---

## 6. 💬 Theonix Messages (`theonix-messages`)

* **Launcher**: `theonix-messages`
* **Source**: `theonix-messages/main.py`

### 6.1 Left Conversation Sidebar
* **Search Chats Input (`QLineEdit`)**: Filters conversations.
* `[+ New Chat]` Action Button: Opens dialog to start direct message or join room.
* **Chat Room List**: Shows avatar, contact name, last message preview, unread badge.

### 6.2 Chat Window & Bottom Composer Bar
* **Header**: Contact Name, E2EE encryption status lock, `[📞 Audio Call]`, `[📹 Video Call]`.
* **AI Quick Replies Bar**: 3 dynamic chip buttons generated by THAID for instant 1-click responses.
* **Composer Input**:
  * `[📎 Attach]` Button: Sends images, files, code snippets.
  * **Text Input (`QTextEdit`)**: Markdown supported.
  * `[🎙️ Voice Note]` Button: Records audio snippet.
  * `[➤ Send]` Button: Transmits encrypted message.

---

## 7. 🧙 Theonix Welcome / Setup Wizard (`theonix-wizard`)

* **Launcher**: `theonix-wizard`
* **Source**: `theonix-wizard/`

### 7.1 Wizard Steps
* **Step 1: Welcome & Language**: Language dropdown, Keyboard layout selector.
* **Step 2: Hardware Drivers**: Auto-detects NVIDIA / AMD / Intel; 1-click `[Install Proprietary Drivers]` button.
* **Step 3: Local AI Setup**: Pick default THAID model (`Llama 3 8B`, `Phi-3 Mini`, `Skip for Now`).
* **Step 4: Desktop Theme**: Select dark/light themes and accent colors.
* **Step 5: Account & Passkey**: Create user password and register master platform passkey.
* **Navigation Footer**:
  * `[Back]` Button
  * `[Skip Step]` Button
  * `[Next ➔]` / `[Finish & Launch Desktop]` Action Button.

---

## 8. 🗃️ Theonix Spotlight Omni-Search (`theonix-search`)

* **Launcher**: `Super+Space` or `theonix-search`
* **Source**: `services/search_service.py`

### 8.1 Floating Spotlight Modal
* **Central Search Query Bar (`QLineEdit`)**: `"Type to search apps, files, settings, and commands..."`
* **Filter Category Chips**: `[All]`, `[Apps]`, `[Files]`, `[Settings]`, `[Actions]`.
* **Results List View (`QListWidget`)**:
  * Icon + Title + Subtitle description + Category tag.
* **Interaction Shortcuts**:
  * `Enter`: Launch app / open file / navigate to settings page.
  * `Super+Enter`: Open containing folder in Theonix Files.
  * `Esc`: Dismiss spotlight overlay.
