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

## Phase 6: Universal Application Compatibility Layer (UACL)
- **Smart File Detection:** Built a Rust-based `SmartDetector` that reads raw magic bytes of any file to automatically identify its format (Windows PE `.exe`/`.msi`, AppImage, `.deb`, `.rpm`, ELF binary) without relying on file extensions.
- **RuntimeManager:** Implemented isolated `WINEPREFIX` management per application in `~/.local/share/theonix-uacl/prefixes/`. Each app gets its own clean Wine environment so they never interfere with each other.
- **DXVK & VKD3D Support:** Integrated automatic DirectX-to-Vulkan translation layer injection for better Windows app and game compatibility.
- **Debian Package Converter:** Built a pipeline using `debtap` to silently convert `.deb` packages into native Arch `.pkg.tar.zst` packages and install them via `pacman` — no terminal needed.
- **SQLite App Registry:** All installed foreign apps are recorded in `~/.config/theonix/uacl.db` with their name, format type, Wine prefix path, and runtime version.
- **Theonix App Manager GUI:** Built a native PyQt6 dark-themed dashboard that reads the database and lets users view, launch, and uninstall all their Windows and foreign applications from a single interface.
- **One-Click Install Dialog (Phase 6.3):** Replaced raw Wine windows with a beautiful frameless progress popup that shows animated step-by-step progress (Detecting → Creating environment → Checking dependencies → Launching) — users never see a terminal or Wine configuration screen.
- **KDE MIME Integration:** Registered the UACL as the system-wide default handler for `.exe`, `.msi`, `.deb`, `.rpm`, and `.AppImage` files. Double-clicking any of these in Dolphin automatically routes them through the UACL launcher.
- **Automated CI/CD Packaging:** Extended the GitHub Actions pipeline to compile the Rust backend, build `debtap` from the AUR, package the Python GUI, and publish everything to the custom `[theonix]` pacman repository.
- **Real-World Testing:** Confirmed Notepad++ installs and runs via Wine. Rufus correctly fails (expected — hardware-level tools cannot be emulated by Wine). AppImage support confirmed operational.
