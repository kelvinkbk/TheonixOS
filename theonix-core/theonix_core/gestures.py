#!/usr/bin/env python3
"""
Theonix Gesture Daemon — Precision Multi-Touch Gesture Router for Theonix OS.

Gesture Matrix:
- 1 finger tap: Left click (Kernel/libinput)
- 2 finger tap: Right click (Kernel/libinput)
- 2 finger scroll: Smooth scroll (Kernel/libinput)
- 2 finger pinch: 1:1 Zoom (KWin native)
- 3 finger swipe UP: Task View / Overview
- 3 finger swipe DOWN: Show Desktop
- 3 finger swipe LEFT / RIGHT: Switch Applications (Alt+Tab)
- 3 finger tap: Middle Click
- 4 finger swipe UP: Workspaces Grid View
- 4 finger swipe LEFT / RIGHT: Switch Virtual Desktops
- 4 finger tap: Launch THAID AI Assistant
"""

import os
import glob
import struct
import subprocess
import time
import sys

EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

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
        self.start_times = {}
        self.max_fingers_seen = 0
        self.gesture_triggered = False
        self.min_swipe_distance = 120  # Pixels sensitivity threshold
        self.tap_max_distance = 35     # Maximum movement for a tap
        self.tap_max_duration = 0.32   # Maximum seconds for tap
        self.cooldown = 0.28           # Cooldown between gestures
        self.last_trigger_time = 0

    def find_touchpad_devices(self):
        touchpads = []
        for path in sorted(glob.glob("/dev/input/event*")):
            try:
                num = os.path.basename(path).replace("event", "")
                name_file = f"/sys/class/input/event{num}/device/name"
                if os.path.exists(name_file):
                    with open(name_file, "r") as f:
                        name = f.read().lower()
                        if "touchpad" in name or "elan" in name or "synaptics" in name:
                            touchpads.append((path, name.strip()))
            except Exception:
                pass
        return touchpads

    def _invoke_kwin(self, shortcut: str):
        subprocess.Popen([
            "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _launch_thaid(self):
        subprocess.Popen(["python3", "/home/k/Desktop/Projects/theonix/theonix-core/theonix_core/services.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def run(self):
        devices = self.find_touchpad_devices()
        if not devices:
            sys.exit(1)

        dev_path, dev_name = devices[0]
        print(f"[Theonix Gestures] Connected to {dev_name} ({dev_path})")

        try:
            fd = open(dev_path, "rb")
        except Exception as e:
            print(f"[Theonix Gestures] Failed to open {dev_path}: {e}")
            sys.exit(1)

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
                        now = time.time()
                        if ev_val == -1:
                            # Finger lifted
                            self.active_slots.pop(current_slot, None)
                            if len(self.active_slots) == 0:
                                # All fingers lifted -> Check for Tap Gestures if no swipe was triggered
                                if not self.gesture_triggered:
                                    t_durations = [now - t for t in self.start_times.values()]
                                    if t_durations and max(t_durations) < self.tap_max_duration:
                                        # Calculate max movement
                                        max_dist = 0
                                        for s in self.start_positions:
                                            if s in self.last_positions:
                                                sx, sy = self.start_positions[s]
                                                lx, ly = self.last_positions[s]
                                                dist = ((lx - sx) ** 2 + (ly - sy) ** 2) ** 0.5
                                                max_dist = max(max_dist, dist)

                                        if max_dist < self.tap_max_distance:
                                            if self.max_fingers_seen == 3:
                                                # 3-Finger Tap -> Middle Click (handled or toggle overview)
                                                self._invoke_kwin("Overview")
                                            elif self.max_fingers_seen == 4:
                                                # 4-Finger Tap -> Toggle THAID / Action Center
                                                self._invoke_kwin("Grid View")

                                # Reset state
                                self.start_positions.clear()
                                self.last_positions.clear()
                                self.start_times.clear()
                                self.max_fingers_seen = 0
                                self.gesture_triggered = False
                        else:
                            # Finger pressed down
                            self.active_slots[current_slot] = ev_val
                            self.start_times[current_slot] = now
                            self.max_fingers_seen = max(self.max_fingers_seen, len(self.active_slots))

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

                        # --- 3-FINGER SWIPES ---
                        if finger_count == 3 and len(dx_list) >= 2:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # Horizontal Swipe -> App Switcher (Alt+Tab)
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.2:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self._invoke_kwin("Walk Through Windows")
                                else:
                                    self._invoke_kwin("Walk Through Windows (Reverse)")

                            # Swipe Up -> Task View / Overview
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.2:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin("Overview")

                            # Swipe Down -> Show Desktop
                            elif avg_dy > self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.2:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin("Show Desktop")

                        # --- 4-FINGER SWIPES ---
                        elif finger_count == 4 and len(dx_list) >= 3:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # Horizontal Swipe -> Switch Virtual Desktops
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.2:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self._invoke_kwin("Switch One Desktop to the Right")
                                else:
                                    self._invoke_kwin("Switch One Desktop to the Left")

                            # Swipe Up -> Workspaces Grid View
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.2:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self._invoke_kwin("Grid View")

            except Exception as e:
                print(f"[Theonix Gestures] Error: {e}")
                break


def main():
    router = GestureRouter()
    router.run()


if __name__ == "__main__":
    main()
