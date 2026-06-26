# Theonix OS - Project History & Milestones

This document serves as a chronological record of the major features, fixes, and milestones achieved during the development of Theonix OS from its inception.

## Phase 1: Core OS Infrastructure & Build Pipeline
- **Custom Arch Linux ISO Pipeline:** Engineered a fully automated, cloud-based ISO generation pipeline using `mkarchiso` running inside Docker, completely managed by GitHub Actions.
- **Custom Pacman Repository:** Established a custom software repository (`[theonix]`) hosted on GitHub Pages, with automated CI/CD pipelines to build and deploy packages (`build-repo.yml`).
- **ISO Build Stability:** Hardened the GitHub Actions build runners against network timeouts during massive (1.8GB+) package downloads by dynamically reprioritizing fast US/EU EndeavourOS mirrors and disabling Pacman's strict download timeouts.

## Phase 2: System Branding & Configuration
- **Theonix Config Package (`theonix-config`):** Created a dedicated pacman package to manage the operating system's internal branding, including logos, Qt stylesheets, and trusted domain configurations.
- **Helper Scripts:** Implemented essential system utilities, including `theonix-enable-ssh` and `force-resolution.sh`, distributed seamlessly through the `theonix-config` package.
- **Conflict Resolution:** Refactored the ISO build process to prevent file conflicts between the static `mkarchiso` template (`airootfs`) and the dynamically installed `theonix-config` pacman package.

## Phase 3: The Installer Experience
- **Custom Calamares Installer:** Integrated and heavily customized the Calamares installer to handle Theonix OS-specific partition layouts, user creation, and post-installation scripting.
- **Wayland Autostart Fix:** Re-engineered the installer launch mechanism to use `pkexec` instead of `sudo`, ensuring the graphical Calamares installer launches flawlessly and automatically on the modern Wayland display server without crashing or falling back to a terminal.
- **Repository Retention:** Fixed a critical bug where the installed system would lose access to the custom `[theonix]` repository by ensuring our custom `pacman.conf` is injected deeply into the live environment's `airootfs` before installation.

## Phase 4: Over-The-Air (OTA) Updates & UI
- **Graphical Update Integration:** Injected `packagekit-qt6` directly into the base ISO package list (`packages.x86_64`), bridging the underlying pacman package manager with the KDE Plasma GUI.
- **KDE Discover & System Settings:** Enabled out-of-the-box support for the KDE Discover App Store and the System Settings "Software Update" module, allowing users to update their OS with a single click.
- **OTA Verification:** Successfully performed a complete end-to-end test of the update pipeline by bumping the `theonix-config` version via GitHub Actions and verifying its seamless deployment to a running VirtualBox installation.

## Phase 5: The AI Core (In Progress)
- **Theonix AI Daemon (`thaid`):** Scaffolded the core intelligence daemon in Rust.
- **Build Fixes:** Resolved complex Link-Time Optimization (LTO) linking errors on GitHub Actions by migrating away from bundled C libraries (e.g., `rusqlite` bundled features) to system-provided dynamic libraries.
- **Architecture:** Laid the groundwork for voice processing (`whisper.rs`, `piper.rs`), hardware management, and deep D-Bus integration (`ai_interface.rs`) to allow the desktop environment to natively communicate with the AI.
