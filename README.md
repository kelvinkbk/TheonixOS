# Theonix OS

## 1. Product Requirements Document (PRD)

### Vision
A modern, lightweight, AI-powered Linux distribution designed for students, developers, creators, and everyday users.

### Goals
- Easy installation
- Beautiful UI
- Fast boot time
- Low resource consumption
- AI-powered assistant
- Secure by default
- Beginner-friendly
- Developer-ready

### Target Users
- **Students**: Online classes, Programming, Office work
- **Developers**: Web Development, AI Development, DevOps
- **Creators**: Video editing, Graphic design, Audio production

### Core Features
- **System**: Linux Kernel, Rolling updates, Secure Boot support
- **Desktop**: Custom Desktop Environment, Dark & Light modes, Modern animations
- **AI Features**: Built-in AI Assistant, Voice Commands, Local AI support
- **Security**: Firewall enabled, Sandboxed applications, Automatic updates

### Success Metrics
- Boot under 15 seconds
- RAM usage under 1GB idle
- Installation under 10 minutes
- User satisfaction > 90%

---

## 2. Technical Requirements Document (TRD)

### Base Distribution
- **Recommended**: Arch Linux (Options considered: Arch Linux, Debian)

### Kernel
- Linux Kernel LTS
- Custom patches
- Security hardening

### Package Manager
- Pacman
- Flatpak
- Snap (optional)

### Desktop Stack
- **Wayland**: Primary Display Server
- **XWayland**: Legacy Support

### System Components
- **Init System**: systemd
- **Bootloader**: GRUB
- **Networking**: NetworkManager
- **Audio**: PipeWire
- **Bluetooth**: BlueZ

### AI Stack
- **Local Models**: Ollama, Llama 3, Gemma
- **Voice**: Whisper, Piper

### Security
- SELinux/AppArmor
- FirewallD
- Secure Boot

### Supported Architectures
- x86_64
- ARM64 (future)

---

## 3. Application Flow

### User Power On
`GRUB Bootloader` -> `Linux Kernel` -> `Systemd Services` -> `Display Manager` -> `Login Screen` -> `Desktop Environment` -> `Home Dashboard` -> `Applications` -> `AI Assistant` -> `User Commands` -> `System Actions`

### Installation Flow
`Boot USB` -> `Language` -> `Keyboard Layout` -> `Disk Selection` -> `User Account` -> `Install Packages` -> `Install Bootloader` -> `Reboot` -> `Setup Wizard` -> `Desktop Ready`

### Update Flow
`Check Updates` -> `Download` -> `Verify Signature` -> `Install` -> `Restart Service` -> `Success`

---

## 4. UI/UX Brief

### Design Philosophy
"Modern, Fast, Minimal"

### Inspiration
macOS, Windows 11, GNOME, KDE Plasma

### Visual Style
- **Theme**: Glassmorphism, Blur Effects, Rounded Corners
- **Colors**:
  - Primary: `#6C63FF`
  - Secondary: `#00D4FF`
  - Background: `#0F1117`
  - Accent: `#00FFAA`

### Layout
- **Top Bar**: Time, Network, Battery, Notifications
- **Dock**: Applications, File Manager, Browser, Terminal
- **Dashboard Widgets**: Weather, Calendar, Notes, AI Assistant

### User Experience Goals
- Learn in <5 minutes
- Reach apps in <2 clicks
- Smooth animations
- Consistent design language

---

## 5. Backend Schema & Architecture

### System Architecture
`Frontend Layer` -> `Desktop Shell` -> `System Services` -> `Linux Kernel` -> `Hardware`

### Core Services
- **User Service**: `id`, `username`, `email`, `password_hash`, `role`
- **Settings Service**: `theme`, `language`, `wallpaper`, `notifications`
- **AI Service**: `model`, `memory`, `voice`, `permissions`
- **Update Service**: `version`, `release_channel`, `status`
- **Package Service**: `name`, `version`, `source`, `installed`

---

## 6. Implementation Plan

### Phase 1 — Core OS Infrastructure & Build Pipeline
- **Tasks**: Setup automated ISO generation with GitHub Actions, establish custom Pacman repository, and harden mirrors for stability.

### Phase 2 — System Branding & Configuration
- **Tasks**: Create the `theonix-config` package to manage custom branding (logos, themes), implement helper scripts, and resolve installer file conflicts.

### Phase 3 — The Installer Experience
- **Tasks**: Customize Calamares for Theonix-specific layouts, ensure Wayland compatibility for the installer GUI via `pkexec`, and inject custom repository configs.

### Phase 4 — Over-The-Air (OTA) Updates & UI
- **Tasks**: Bridge Pacman with KDE Discover and System Settings via PackageKit, enabling one-click seamless graphical updates.

### Phase 5 — AI Integration (Voice Assistant)
- **Tasks**: Develop the completely offline THAID AI Assistant, integrating Ollama (LLM), Whisper (STT), and Piper (TTS) with a custom D-Bus Rust daemon and QML UI.

### Phase 6 — Universal Application Compatibility Layer (UACL)
- **Tasks**: Build a translation layer that automatically handles Windows `.exe`/`.msi` files (via isolated Wine prefixes), `.deb`/`.rpm` conversions, and AppImages through a unified native App Manager GUI.

### Phase 7 — Stable Release & Community
- **Release Targets**: ISO Download, Official Website, Documentation Portal, Community Forums, and Theonix OS 1.0 Release.

---

## Suggested Tech Stack
| Component | Technology |
| --- | --- |
| **Base Distro** | Arch Linux |
| **Desktop** | KDE Plasma Fork |
| **Package Manager** | Pacman |
| **Installer** | Calamares |
| **AI** | Ollama |
| **Voice** | Whisper + Piper |
| **UI Toolkit** | Qt6 |
| **Display Server** | Wayland |
| **Build System** | ArchISO |
| **Security** | AppArmor |
