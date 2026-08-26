#!/usr/bin/env python3
"""
Theonix OS — Input & Touchpad Gesture Service (org.theonix.Input)
Decoupled background daemon managing touchpad gestures, mouse preferences,
hotkeys, and compositor gesture integration for Theonix OS.
"""

import sys
import os
import glob
import json
import subprocess
import configparser
from typing import Dict, Any, List

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSlot, pyqtSignal
from PyQt6.QtDBus import QDBusConnection


CONFIG_PATH = os.path.expanduser("~/.config/theonix/input.json")
KCMINPUTRC_PATH = os.path.expanduser("~/.config/kcminputrc")
KWINRC_PATH = os.path.expanduser("~/.config/kwinrc")


DEFAULT_CONFIG: Dict[str, Any] = {
    "tap_to_click": True,
    "tap_and_drag": True,
    "natural_scroll": True,
    "disable_while_typing": True,
    "pointer_speed": 6,
    "gestures": {
        "swipe_3_up": "overview",
        "swipe_3_down": "show_desktop",
        "swipe_3_left": "switch_apps",
        "swipe_3_right": "switch_apps",
        "swipe_4_left": "prev_desktop",
        "swipe_4_right": "next_desktop",
        "pinch_4": "omni_search"
    }
}


class InputService(QObject):
    gestureDetected = pyqtSignal(str, str)  # gesture_name, action_executed
    configChanged = pyqtSignal(str)         # json_config

    def __init__(self):
        super().__init__()
        self._config = self._load_config()
        self._sync_to_system()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return cfg
            except Exception as e:
                print(f"[InputService] Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"[InputService] Error saving config: {e}")

    def _sync_to_system(self):
        """Synchronizes input settings to KDE/Wayland compositor configs and reloads kwin."""
        tap_click = self._config.get("tap_to_click", True)
        tap_drag = self._config.get("tap_and_drag", True)
        natural_scroll = self._config.get("natural_scroll", True)
        dwt = self._config.get("disable_while_typing", True)
        speed = self._config.get("pointer_speed", 6)
        speed_val = (speed - 5) * 0.08

        # 1. Update kcminputrc
        try:
            config = configparser.ConfigParser(interpolation=None, strict=False)
            if os.path.exists(KCMINPUTRC_PATH):
                config.read(KCMINPUTRC_PATH)
            
            for section in config.sections():
                if "Libinput" in section and ("Touchpad" in section or "touchpad" in section):
                    config[section]["Enabled"] = "true"
                    config[section]["TapToClick"] = "true" if tap_click else "false"
                    config[section]["TapAndDrag"] = "true" if tap_drag else "false"
                    config[section]["NaturalScroll"] = "true" if natural_scroll else "false"
                    config[section]["ScrollTwoFinger"] = "true"
                    config[section]["ClickMethod"] = "2"
                    config[section]["DisableWhileTyping"] = "true" if dwt else "false"
                    config[section]["PointerAcceleration"] = f"{speed_val:.3f}"
                    config[section]["PointerAccelerationProfile"] = "1"
            
            os.makedirs(os.path.dirname(KCMINPUTRC_PATH), exist_ok=True)
            with open(KCMINPUTRC_PATH, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"[InputService] kcminputrc sync error: {e}")

        # 2. Update kwinrc for Wayland precision gestures
        try:
            config = configparser.ConfigParser(interpolation=None, strict=False)
            if os.path.exists(KWINRC_PATH):
                config.read(KWINRC_PATH)
            if "Touchpad" not in config:
                config["Touchpad"] = {}
            config["Touchpad"]["GesturePinch"] = "true"
            config["Touchpad"]["GestureSwipe"] = "true"
            
            os.makedirs(os.path.dirname(KWINRC_PATH), exist_ok=True)
            with open(KWINRC_PATH, "w") as f:
                config.write(f)
            
            # Reload KWin config over D-Bus
            subprocess.run(
                ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[InputService] kwinrc sync error: {e}")

    @pyqtSlot(result=bool)
    def RecoverTouchpad(self) -> bool:
        """Forces unfreezing, power restore, and re-enabling of Touchpad after lid close/open or sleep."""
        print("[InputService] Executing Touchpad Lid/Wake Recovery...")
        try:
            # 1. Ensure runtime power management is 'on' for all I2C and input devices
            for p in glob.glob("/sys/bus/i2c/devices/*/power/control"):
                try:
                    with open(p, "w") as f:
                        f.write("on")
                except Exception:
                    pass

            for p in glob.glob("/sys/devices/platform/AMDI0010*/*/power/control"):
                try:
                    with open(p, "w") as f:
                        f.write("on")
                except Exception:
                    pass

            # 2. Re-enable all Touchpad input devices in KWin Wayland over D-Bus
            try:
                out = subprocess.run(["busctl", "--user", "tree", "org.kde.KWin"], capture_output=True, text=True, timeout=2)
                for line in out.stdout.splitlines():
                    if "/org/kde/KWin/InputDevice/event" in line:
                        obj_path = line.strip().split()[-1]
                        subprocess.run(
                            ["busctl", "--user", "set-property", "org.kde.KWin", obj_path, "org.kde.KWin.InputDevice", "enabled", "b", "true"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                        )
                        subprocess.run(
                            ["busctl", "--user", "set-property", "org.kde.KWin", obj_path, "org.kde.KWin.InputDevice", "tapToClick", "b", "true"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1
                        )
            except Exception as e:
                print(f"[InputService] KWin D-Bus enable error: {e}")

            # 3. Ensure Wi-Fi PCIe controller stays awake and connected
            for p in glob.glob("/sys/bus/pci/devices/*/power/control"):
                try:
                    with open(p, "w") as f:
                        f.write("on")
                except Exception:
                    pass

            for p in glob.glob("/sys/bus/pci/devices/*/power/wakeup"):
                try:
                    with open(p, "w") as f:
                        f.write("enabled")
                except Exception:
                    pass

            # 4. Check Wi-Fi state and trigger connection if dropped
            try:
                nm_res = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True, timeout=1)
                if "enabled" not in nm_res.stdout.lower():
                    subprocess.run(["nmcli", "radio", "wifi", "on"], stdout=subprocess.DEVNULL, timeout=2)
            except Exception:
                pass

            # 5. Resync settings to KWin
            self._sync_to_system()
            return True
        except Exception as e:
            print(f"[InputService] RecoverTouchpad error: {e}")
            return False

    @pyqtSlot(result=str)
    def GetGestureConfig(self) -> str:
        """Returns the active touchpad and gesture configuration as JSON."""
        return json.dumps(self._config)

    @pyqtSlot(str, result=bool)
    def SetGestureConfig(self, config_json: str) -> bool:
        """Updates and applies the gesture configuration."""
        try:
            new_cfg = json.loads(config_json)
            self._config.update(new_cfg)
            self._save_config()
            self._sync_to_system()
            self.configChanged.emit(json.dumps(self._config))
            return True
        except Exception as e:
            print(f"[InputService] SetGestureConfig error: {e}")
            return False

    @pyqtSlot(str, result=bool)
    def TriggerGestureAction(self, gesture_name: str) -> bool:
        """Executes the mapped system action for a given gesture."""
        gestures = self._config.get("gestures", {})
        action = gestures.get(gesture_name, "")
        if not action:
            return False

        print(f"[InputService] Triggering action '{action}' for gesture '{gesture_name}'")

        if action == "overview":
            subprocess.Popen(["qdbus6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", "Overview"])
        elif action == "show_desktop":
            subprocess.Popen(["qdbus6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", "Show Desktop"])
        elif action == "switch_apps":
            subprocess.Popen(["qdbus6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", "Walk Through Windows"])
        elif action == "next_desktop":
            subprocess.Popen(["qdbus6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", "Switch to Next Desktop"])
        elif action == "prev_desktop":
            subprocess.Popen(["qdbus6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", "Switch to Previous Desktop"])
        elif action == "omni_search":
            subprocess.Popen(["qdbus6", "org.theonix.Search", "/org/theonix/Search", "Toggle"])
        elif action == "thaid":
            subprocess.Popen(["qdbus6", "org.theonix.AIGUI", "/org/theonix/AIGUI", "toggleListening"])
        else:
            return False

        self.gestureDetected.emit(gesture_name, action)
        return True

    @pyqtSlot(result=str)
    def ListAvailableActions(self) -> str:
        """Returns the list of bindable system actions."""
        actions = [
            {"id": "overview", "name": "Task View (Window Overview)", "desc": "Expose all open windows across workspaces"},
            {"id": "show_desktop", "name": "Show Desktop", "desc": "Minimize/restore all active windows"},
            {"id": "switch_apps", "name": "App Switcher", "desc": "Fast cycle through open applications"},
            {"id": "next_desktop", "name": "Next Workspace", "desc": "Slide to the next virtual desktop"},
            {"id": "prev_desktop", "name": "Previous Workspace", "desc": "Slide to previous virtual desktop"},
            {"id": "omni_search", "name": "Global Omni-Search", "desc": "Open Spotlight search overlay"},
            {"id": "thaid", "name": "THAID AI Assistant", "desc": "Trigger voice listening orb"},
        ]
        return json.dumps(actions)


class LidWatcher(QObject):
    """Monitors systemd-logind LidClosed and PrepareForSleep signals to auto-recover Touchpad."""
    def __init__(self, input_service: InputService):
        super().__init__()
        self.service = input_service
        self.last_lid_closed = False

        from PyQt6.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._check_lid_state)
        self.timer.start(2000)

    @pyqtSlot(bool)
    def onPrepareForSleep(self, sleeping: bool):
        if not sleeping:
            print("[LidWatcher] System resume/wake detected! Recovering touchpad...")
            self.service.RecoverTouchpad()

    def _check_lid_state(self):
        try:
            r = subprocess.run(
                ["busctl", "get-property", "org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager", "LidClosed"],
                capture_output=True, text=True, timeout=1
            )
            is_closed = "true" in r.stdout.lower()
            if self.last_lid_closed and not is_closed:
                print("[LidWatcher] Lid opened detected! Recovering touchpad...")
                self.service.RecoverTouchpad()
            self.last_lid_closed = is_closed
        except Exception:
            pass


def main():
    app = QCoreApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    service = InputService()
    lid_watcher = LidWatcher(service)

    # Listen to System Sleep/Wake signal
    system_bus = QDBusConnection.systemBus()
    system_bus.connect(
        "org.freedesktop.login1", "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager", "PrepareForSleep",
        lid_watcher.onPrepareForSleep
    )

    if not bus.registerService("org.theonix.Input"):
        print("[InputService] Failed to register D-Bus service 'org.theonix.Input'")
        sys.exit(1)

    if not bus.registerObject("/org/theonix/Input", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[InputService] Failed to register D-Bus object at '/org/theonix/Input'")
        sys.exit(1)

    print("[InputService] Theonix Input Service active on org.theonix.Input [/org/theonix/Input] with Lid Recovery")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
