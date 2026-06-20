#!/usr/bin/env python3
# =============================================================================
# Theonix OS — Calamares Post-Install Module
# =============================================================================
# This module runs inside the installed system's chroot after all packages
# are installed. It configures Theonix-specific services, creates the
# first-boot wizard marker, and hardens the installed system.
#
# Reference: https://github.com/calamares/calamares/wiki/Module-Python
# =============================================================================

import os
import subprocess
import shutil
import libcalamares  # noqa: E402 – provided by Calamares at runtime


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_in_chroot(cmd: list[str]) -> tuple[int, str]:
    """Run a command inside the chroot of the target system."""
    chroot = libcalamares.globalstorage.value("rootMountPoint")
    full_cmd = ["chroot", chroot] + cmd
    result = subprocess.run(
        full_cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode, result.stdout + result.stderr


def write_to_chroot(relative_path: str, content: str, mode: int = 0o644) -> None:
    """Write a file into the chroot target system."""
    chroot = libcalamares.globalstorage.value("rootMountPoint")
    full_path = os.path.join(chroot, relative_path.lstrip("/"))
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(full_path, mode)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run():  # noqa: C901  (acceptable complexity for an installer module)
    """Theonix post-install configuration."""
    libcalamares.utils.debug("==> theonix-postinstall: Starting")

    # ---- 1. Enable essential services ---------------------------------------
    services_enable = [
        "NetworkManager",
        "sddm",
        "firewalld",
        "apparmor",
        "fstrim.timer",       # weekly SSD trim
        "paccache.timer",     # weekly package cache cleanup
        "snapper-timeline.timer",
        "snapper-cleanup.timer",
        "grub-btrfsd.service",
    ]

    for service in services_enable:
        rc, out = run_in_chroot(["systemctl", "enable", service])
        if rc != 0:
            libcalamares.utils.warning(f"Failed to enable {service}: {out}")
        else:
            libcalamares.utils.debug(f"  Enabled: {service}")

    # ---- 2. Mask insecure / unnecessary services in installed system --------
    services_mask = [
        "sshd",             # user must explicitly enable SSH
        "livecd-talk",      # live-ISO only
        "choose-mirror",    # live-ISO only
        "pacman-init",      # live-ISO only
    ]

    for service in services_mask:
        rc, _ = run_in_chroot(["systemctl", "mask", service])
        if rc == 0:
            libcalamares.utils.debug(f"  Masked: {service}")

    # ---- 3. Set SDDM theme --------------------------------------------------
    sddm_conf = "[Theme]\nCurrent=theonix\n"
    write_to_chroot("/etc/sddm.conf.d/theonix.conf", sddm_conf)
    libcalamares.utils.debug("  SDDM theme set to: theonix")

    # ---- 4. Set Plymouth theme ----------------------------------------------
    rc, out = run_in_chroot(
        ["plymouth-set-default-theme", "--rebuild-initrd", "theonix"]
    )
    if rc != 0:
        libcalamares.utils.warning(f"Plymouth theme set failed (non-fatal): {out}")

    # ---- 5. Configure journald limits ---------------------------------------
    journald_conf = (
        "[Journal]\n"
        "SystemMaxUse=500M\n"
        "SystemKeepFree=1G\n"
        "MaxFileSec=1month\n"
        "Compress=yes\n"
    )
    write_to_chroot("/etc/systemd/journald.conf.d/theonix.conf", journald_conf)
    libcalamares.utils.debug("  journald limits configured")

    # ---- 6. Configure tmpfs /tmp -------------------------------------------
    rc, _ = run_in_chroot(["systemctl", "enable", "tmp.mount"])
    libcalamares.utils.debug("  tmpfs /tmp enabled")

    # ---- 7. Set GRUB defaults for the installed system ---------------------
    grub_defaults = (
        'GRUB_DEFAULT=0\n'
        'GRUB_TIMEOUT=3\n'
        'GRUB_TIMEOUT_STYLE=hidden\n'
        'GRUB_DISTRIBUTOR="Theonix OS"\n'
        'GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 systemd.show_status=auto '
        'rd.udev.log_level=3 apparmor=1 security=apparmor '
        'lsm=landlock,lockdown,yama,integrity,apparmor,bpf splash"\n'
        'GRUB_CMDLINE_LINUX=""\n'
        'GRUB_PRELOAD_MODULES="part_gpt part_msdos"\n'
        'GRUB_TERMINAL_INPUT=console\n'
        'GRUB_TERMINAL_OUTPUT=console\n'
        'GRUB_GFXMODE=auto\n'
        'GRUB_GFXPAYLOAD_LINUX=keep\n'
        'GRUB_DISABLE_RECOVERY=false\n'
    )
    write_to_chroot("/etc/default/grub", grub_defaults)

    # Regenerate GRUB config
    rc, out = run_in_chroot(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
    if rc != 0:
        libcalamares.utils.warning(f"grub-mkconfig warning (may be OK): {out}")

    # ---- 8. Configure snapper for root subvolume ---------------------------
    rc, out = run_in_chroot(
        ["snapper", "--no-dbus", "-c", "root", "create-config", "/"]
    )
    if rc != 0:
        libcalamares.utils.warning(f"snapper create-config: {out}")

    # ---- 9. Create the first-boot wizard marker ----------------------------
    # The Setup Wizard reads this file; when it completes, it removes it.
    write_to_chroot("/etc/theonix/firstboot", "", mode=0o644)
    libcalamares.utils.debug("  First-boot wizard marker created")

    # ---- 10. Write Theonix OS os-release -----------------------------------
    # Augment the distro info provided by Arch base
    os_release_extra = (
        '\n# Theonix OS additions\n'
        'THEONIX_VERSION="1.0"\n'
        'THEONIX_CODENAME="Orion"\n'
        'THEONIX_WEBSITE="https://theonix.org"\n'
    )
    chroot = libcalamares.globalstorage.value("rootMountPoint")
    os_release_path = os.path.join(chroot, "etc/os-release")
    with open(os_release_path, "a", encoding="utf-8") as f:
        f.write(os_release_extra)

    # ---- 11. Set package cache cleanup policy ------------------------------
    paccache_conf = "[paccache]\nKEEP=2\n"
    write_to_chroot("/etc/paccache.conf", paccache_conf)

    libcalamares.utils.debug("==> theonix-postinstall: Complete")
    return None
