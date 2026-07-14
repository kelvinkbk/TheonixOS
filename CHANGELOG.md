# Changelog

All notable changes to Theonix OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-14 "Genesis"

### Added
- **Core OS Foundation**: Built upon a rolling-release Arch Linux base for cutting-edge packages and maximum performance.
- **Desktop Environment**: Shipped with KDE Plasma 6 running natively on Wayland.
- **Custom Installer**: Integrated a fully branded, guided Calamares installer for a seamless setup experience.
- **Theonix Repository**: Established an independent custom `pacman` repository for delivering Theonix-specific tools and updates.
- **Premium Aesthetics**:
  - Custom glassmorphism SDDM login screen.
  - Branded Plymouth boot splash animations.
  - Custom GRUB bootloader theme.
  - Default dark-mode Plasma "Theonix" look-and-feel package.
- **System Tooling**:
  - Integrated Fastfetch with Theonix OS ASCII branding for system information.
  - Pre-configured `btrfs` file system support.
  - Built-in AppArmor and UFW/firewalld configurations for enhanced security.
- **AI Integration**: Laid the groundwork for the Theonix AI Daemon (THAID) to provide on-device intelligent assistance.

### Fixed
- Resolved `pacstrap` file conflicts between manual filesystem staging and the automated `theonix-branding` package.
- Corrected UTF-16 encoding corruption when building `packages.x86_64` payload.
