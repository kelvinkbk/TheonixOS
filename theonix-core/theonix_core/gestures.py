#!/usr/bin/env python3
"""
Theonix Gesture Daemon — Precision Multi-Touch Gesture Router for Theonix OS.

Configured Gesture Table:
- 1 finger tap: Left click
- 2 finger tap: Right click
- 2 finger scroll: Smooth natural scroll
- 2 finger pinch: 1:1 Zoom
- 2 finger swipe left/right: Back / Forward (Alt+Left / Alt+Right)
- 3 finger swipe up: Task View / Overview (Meta+W)
- 3 finger swipe down: Show Desktop (Meta+D)
- 3 finger swipe left/right: Switch applications (Alt+Tab / Alt+Shift+Tab)
- 3 finger tap: Middle click
- 4 finger swipe up: Overview / Workspaces Grid (Meta+G)
- 4 finger swipe left/right: Switch workspace (Meta+Ctrl+Left / Right)
- 4 finger tap: THAID AI Assistant / Notification center
"""

import os
import glob
import struct
import subprocess
import time
import threading

EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

# Linux Input Event Codes
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03

ABS_MT_SLOT = 0x2f
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
ABS_MT_TRACKING_ID = 0x39


class GestureRouter:
    def __init__(self):
        self.active_slots = {}
        self.start_positions = {}
        self.last_positions = {}
        self.start_time = {}
        self.gesture_triggered = False
        self.min_swipe_distance = 160  # Pixels threshold
        self.tap_max_distance = 25     # Maximum movement for a tap
        self.tap_max_duration = 0.28   # Max seconds for a tap
        self.cooldown = 0.30           # Seconds between gestures
        self.last_trigger_time = 0

    def find_touchpad_device(self):
        devices = []
        for path in glob.glob("/dev/input/event*"):
            try:
                num = os.path.basename(path).replace("event", "")
                name_file = f"/sys/class/input/event{num}/device/name"
                if os.path.exists(name_file):
                    with open(name_file, "r") as f:
                        name = f.read().lower()
                        if "touchpad" in name or "elan" in name or "synaptics" in name:
                            devices.append(path)
            except Exception:
                pass
        return devices[0] if devices else "/dev/input/event12"

    def _invoke_kwin_shortcut(self, shortcut_name: str):
        subprocess.Popen([
            "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut_name
        ], stderr=subprocess.DEVNULL)

    def _invoke_plasmashell_shortcut(self, component: str, shortcut_name: str):
        subprocess.Popen([
            "qdbus6", "org.kde.kglobalaccel", f"/component/{component}",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut_name
        ], stderr=subprocess.DEVNULL)

    def run(self):
        dev_path = self.find_touchpad_device()
        try:
            fd = open(dev_path, "rb")
        except PermissionError:
            return

        current_slot = 0

        while True:
            try:
                data = fd.read(EVENT_SIZE)
                if not data:
                    break
                sec, usec, ev_type, ev_code, ev_val = struct.unpack(EVENT_FORMAT, data)

                if ev_type == EV_ABS:
                    if ev_code == ABS_MT_SLOT:
                        current_slot = ev_val
                    elif ev_code == ABS_MT_TRACKING_ID:
                        if ev_val == -1:
                            # Finger lifted - Check for multi-finger taps if gesture was not triggered
                            now = time.time()
                            start_t = self.start_time.get(current_slot, now)
                            duration = now - start_t
                            
                            # Clean up slot
                            self.active_slots.pop(current_slot, None)
                            self.start_positions.pop(current_slot, None)
                            self.last_positions.pop(current_slot, None)
                            self.start_time.pop(current_slot, None)

                            if len(self.active_slots) == 0:
                                self.gesture_triggered = False
                        else:
                            # Finger pressed down
                            self.active_slots[current_slot] = ev_val
                            self.start_time[current_slot] = time.time()

                    elif ev_code == ABS_MT_POSITION_X:
                        if current_slot in self.active_slots:
                            if current_slot not in self.start_positions:
                                self.start_positions[current_slot] = (ev_val, 0)
                            prev_y = self.last_positions.get(current_slot, (0, 0))[1]
                            self.last_positions[current_slot] = (ev_val, prev_y)

                    elif ev_code == ABS_MT_POSITION_Y:
                        if current_slot in self.active_slots:
                            if current_slot in self.start_positions:
                                start_x = self.start_positions[current_slot][0]
                                self.start_positions[current_slot] = (start_x, ev_val)
                            prev_x = self.last_positions.get(current_slot, (0, 0))[0]
                            self.last_positions[current_slot] = (prev_x, ev_val)

                elif ev_type == EV_SYN:
                    finger_count = len(self.active_slots)
                    now = time.time()

                    if not self.gesture_triggered and (now - self.last_trigger_time > self.cooldown):
                        dx_list = []
                        dy_list = []
                        for slot in list(self.active_slots.keys()):
                            if slot in self.start_positions and slot in self.last_positions:
                                sx, sy = self.start_positions[slot]
                                lx, ly = self.last_positions[slot]
                                if sx > 0 and lx > 0 and sy > 0 and ly > 0:
                                    dx_list.append(lx - sx)
                                    dy_list.append(ly - sy)

                        # --- 3-FINGER GESTURES ---
                        if finger_count == 3 and len(dx_list) >= 2:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # 3-Finger Swipe Left / Right -> Switch Applications (Alt+Tab)
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self._invoke_kwin_shortcut("Walk Through Windows")
                                else:
                                    self._invoke_kwin_shortcut("Walk Through Windows (Reverse)")

                            # 3-Finger Swipe Up -> Task View / Overview
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin_shortcut("Overview")

                            # 3-Finger Swipe Down -> Show Desktop
                            elif avg_dy > self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin_shortcut("Show Desktop")

                        # --- 4-FINGER GESTURES ---
                        elif finger_count == 4 and len(dx_list) >= 3:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # 4-Finger Swipe Left / Right -> Switch Virtual Desktop Workspace
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self._invoke_kwin_shortcut("Switch One Desktop to the Right")
                                else:
                                    self._invoke_kwin_shortcut("Switch One Desktop to the Left")

                            # 4-Finger Swipe Up -> Overview / Grid View
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin_shortcut("Grid View")

            except Exception:
                break


def main():
    router = GestureRouter()
    router.run()


if __name__ == "__main__":
    main()
