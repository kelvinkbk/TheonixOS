# Theonix OS Architecture

## System Overview

Theonix OS is designed as a modular, high-performance Linux distribution. It utilizes an Arch Linux base for rolling releases and bleeding-edge packages, combined with a highly customized graphical stack and an integrated AI service daemon.

### 1. Base Layer (Kernel & Hardware)
- **Kernel**: Linux LTS kernel with custom patches for low-latency audio/video and strict AppArmor confinement.
- **Init System**: `systemd` to manage service lifecycles, user sessions, and hardware event handling.

### 2. Core Services
- **NetworkManager**: Manages network states and connections.
- **PipeWire & WirePlumber**: Audio/video routing and policy management.
- **BlueZ**: Bluetooth stack.
- **Theonix AI Daemon (`thaid`)**: A local background service managing Ollama, Whisper, and Piper. Exposes a D-Bus/REST API for the desktop environment to invoke AI tasks.

### 3. Display Stack
- **Wayland Compositor**: Primary display server protocol.
- **KWin (Plasma Fork) / Custom wlroots**: Window manager and compositor.
- **XWayland**: Compatibility layer for legacy X11 applications.

### 4. Desktop Environment (Theonix Shell)
- **Framework**: Qt6 with QML for accelerated, modern user interfaces.
- **Styling**: Global Qt Style Sheets (`.qss`) and QML theme definitions providing glassmorphism and smooth animations.
- **Components**:
  - **Top Bar**: System tray, global menu, and AI status.
  - **Dock**: Application launcher.
  - **Dashboard**: Widget host and central hub.

### 5. Application Sandboxing & Security
- **AppArmor**: Profiles enforced by default on internet-facing applications (browsers, network tools).
- **Flatpak**: Preferred method for distributing third-party graphical applications to ensure dependency isolation and sandbox constraints.

## Inter-Process Communication (IPC)
Theonix OS heavily relies on **D-Bus** for communication between the system services and the user space.
- Example: The Dashboard UI queries `thaid` via D-Bus to transcribe voice or generate text.

## Package Management
- **pacman**: Core OS updates and native packages.
- **Flatpak**: User-level applications.
- **Theonix Store**: A unified GUI frontend (Discover fork or custom) that manages both pacman and flatpak repositories.
