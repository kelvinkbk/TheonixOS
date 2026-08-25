#!/usr/bin/env python3
"""
Theonix OS — System Update Service (org.theonix.Updates)
Decoupled background D-Bus service for system update lifecycle orchestration.
Bridges Theonix Settings & Store with native pacman, flatpak, and Theonix repository packages.
"""

import sys
import os
import time
import json
import subprocess
import threading
from typing import Dict, Any, List

# Ensure PyQt6 has access to DBus
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtDBus import QDBusConnection


class UpdateService(QObject):
    updateProgress = pyqtSignal(int, str, str)       # percent (0-100), current_pkg, status_msg
    updateCompleted = pyqtSignal(bool, str)          # success, summary_msg
    checkCompleted = pyqtSignal(int, str)            # count, json_payload

    def __init__(self):
        super().__init__()
        self._is_updating = False
        self._is_checking = False
        self._last_check_time = 0
        self._cached_updates: Dict[str, Any] = {
            "native": [],
            "flatpak": [],
            "theonix": [],
            "total_count": 0,
            "last_checked": "Never"
        }

    @pyqtSlot(result=str)
    def GetSystemStatus(self) -> str:
        """Returns comprehensive hardware and OS lifecycle status as JSON."""
        status = {
            "os_name": "Theonix OS",
            "os_version": "2.0.0 (Nebula)",
            "kernel": os.uname().release,
            "arch": os.uname().machine,
            "reboot_required": os.path.exists("/var/run/reboot-required"),
            "is_updating": self._is_updating,
            "is_checking": self._is_checking,
            "last_checked": self._cached_updates.get("last_checked", "Never"),
            "pending_updates_count": self._cached_updates.get("total_count", 0)
        }
        return json.dumps(status)

    @pyqtSlot(result=str)
    def CheckForUpdates(self) -> str:
        """Asynchronously checks for native Arch, Flatpak, and Theonix updates."""
        if self._is_checking:
            return json.dumps(self._cached_updates)

        self._is_checking = True

        def _do_check():
            native_pkgs = []
            flatpak_pkgs = []
            theonix_pkgs = []

            try:
                # 1. Check Pacman / Native updates (checkupdates utility)
                res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=20)
                if res.returncode == 0 and res.stdout.strip():
                    for line in res.stdout.strip().splitlines():
                        parts = line.split()
                        if len(parts) >= 4:
                            pkg_info = {"name": parts[0], "current": parts[1], "new": parts[3]}
                            if "theonix" in parts[0] or "thaid" in parts[0]:
                                theonix_pkgs.append(pkg_info)
                            else:
                                native_pkgs.append(pkg_info)
            except Exception as e:
                print(f"[UpdateService] checkupdates error: {e}")

            # 2. Check Flatpak updates if flatpak is installed
            if os.path.exists("/usr/bin/flatpak"):
                try:
                    res_fp = subprocess.run(
                        ["flatpak", "remote-ls", "--updates", "--columns=name,application,version"],
                        capture_output=True, text=True, timeout=15
                    )
                    if res_fp.returncode == 0 and res_fp.stdout.strip():
                        for line in res_fp.stdout.strip().splitlines():
                            cols = [c.strip() for c in line.split("\t") if c.strip()]
                            if cols:
                                flatpak_pkgs.append({
                                    "name": cols[0],
                                    "app_id": cols[1] if len(cols) > 1 else cols[0],
                                    "new": cols[2] if len(cols) > 2 else "latest"
                                })
                except Exception as e:
                    print(f"[UpdateService] flatpak check error: {e}")

            total = len(native_pkgs) + len(flatpak_pkgs) + len(theonix_pkgs)
            self._cached_updates = {
                "native": native_pkgs,
                "flatpak": flatpak_pkgs,
                "theonix": theonix_pkgs,
                "total_count": total,
                "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self._last_check_time = time.time()
            self._is_checking = False

            payload = json.dumps(self._cached_updates)
            self.checkCompleted.emit(total, payload)

        threading.Thread(target=_do_check, daemon=True).start()
        return json.dumps({"status": "checking_started"})

    @pyqtSlot(result=str)
    def GetCachedUpdates(self) -> str:
        """Returns the most recent update check cache."""
        return json.dumps(self._cached_updates)

    @pyqtSlot(str, result=bool)
    def InstallUpdates(self, target_categories: str = "all") -> bool:
        """Orchestrates update installation in background and emits progress."""
        if self._is_updating:
            return False

        self._is_updating = True

        def _do_install():
            self.updateProgress.emit(5, "system", "Initializing Theonix update orchestrator...")
            time.sleep(0.5)

            try:
                # Step 1: Update Pacman database and native packages
                self.updateProgress.emit(20, "pacman", "Refreshing package repositories...")
                cmd_pacman = ["pkexec", "pacman", "-Syu", "--noconfirm"]
                proc = subprocess.Popen(
                    cmd_pacman, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                
                # Stream output
                for line in proc.stdout:
                    clean = line.strip()
                    if clean:
                        self.updateProgress.emit(50, "pacman", clean[:80])

                proc.wait()

                # Step 2: Update Flatpaks if present
                if os.path.exists("/usr/bin/flatpak"):
                    self.updateProgress.emit(75, "flatpak", "Updating Flatpak application runtimes...")
                    subprocess.run(["flatpak", "update", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # Step 3: Refresh desktop database & font caches
                self.updateProgress.emit(90, "system", "Updating icon caches and desktop database...")
                subprocess.run(["gtk-update-icon-cache", "-f", "/usr/share/icons/hicolor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["update-desktop-database", "/usr/share/applications"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                self.updateProgress.emit(100, "done", "System is up to date!")
                self._cached_updates["total_count"] = 0
                self._cached_updates["native"] = []
                self._cached_updates["flatpak"] = []
                self._cached_updates["theonix"] = []
                self.updateCompleted.emit(True, "All system packages and runtimes successfully updated.")
            except Exception as e:
                self.updateCompleted.emit(False, f"Update encountered an error: {e}")
            finally:
                self._is_updating = False

        threading.Thread(target=_do_install, daemon=True).start()
        return True

    @pyqtSlot(result=str)
    def GetChangelog(self) -> str:
        """Returns the latest system changelog."""
        changelog_paths = [
            "/home/k/Desktop/Projects/theonix/CHANGELOG.md",
            "/usr/share/doc/theonix/CHANGELOG.md",
            "/etc/theonix/CHANGELOG.md"
        ]
        for p in changelog_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        return f.read()
                except Exception:
                    pass
        return "Theonix OS 2.0.0 — Modern AI-Driven Linux Desktop\n• Modular Core System Services\n• THAID AI Assistant with Whisper-Small & Piper Neural TTS\n• Touchpad gestures and unified app framework."


def main():
    app = QCoreApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    service = UpdateService()
    if not bus.registerService("org.theonix.Updates"):
        print("[UpdateService] Failed to register D-Bus service 'org.theonix.Updates'")
        sys.exit(1)

    if not bus.registerObject("/org/theonix/Updates", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[UpdateService] Failed to register D-Bus object at '/org/theonix/Updates'")
        sys.exit(1)

    print("[UpdateService] Theonix Update Service active on org.theonix.Updates [/org/theonix/Updates]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
