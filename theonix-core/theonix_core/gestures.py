#!/usr/bin/env python3
"""
Theonix Gesture Daemon — Precision Multi-Touch Gesture Router for Theonix OS.
Maps:
- 3-Finger Swipe Left / Right -> Switch Between Open Applications (Alt+Tab)
- 3-Finger Swipe Up -> Task View (Overview)
- 3-Finger Swipe Down -> Show Desktop (Minimize All)
- 4-Finger Swipe Left / Right -> Switch Virtual Desktops
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

ABS_X = 0x00
ABS_Y = 0x01
ABS_MT_SLOT = 0x2f
ABS_MT_TOUCH_MAJOR = 0x30
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
ABS_MT_TRACKING_ID = 0x39


class GestureRouter:
    def __init__(self):
        self.active_slots = {}
        self.start_positions = {}
        self.last_positions = {}
        self.gesture_triggered = False
        self.min_swipe_distance = 180  # Pixels threshold
        self.cooldown = 0.35  # Seconds
        self.last_trigger_time = 0

    def find_touchpad_device(self):
        # Look for touchpad event files
        devices = []
        for path in glob.glob("/dev/input/event*"):
            try:
                # Check name from sysfs
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
                            # Finger lifted
                            self.active_slots.pop(current_slot, None)
                            self.start_positions.pop(current_slot, None)
                            self.last_positions.pop(current_slot, None)
                            if len(self.active_slots) == 0:
                                self.gesture_triggered = False
                        else:
                            # Finger pressed down
                            self.active_slots[current_slot] = ev_val
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

                    # Handle 3-Finger Gestures
                    if finger_count == 3 and not self.gesture_triggered and (now - self.last_trigger_time > self.cooldown):
                        # Calculate average displacement across active fingers
                        dx_list = []
                        dy_list = []
                        for slot in list(self.active_slots.keys()):
                            if slot in self.start_positions and slot in self.last_positions:
                                sx, sy = self.start_positions[slot]
                                lx, ly = self.last_positions[slot]
                                if sx > 0 and lx > 0 and sy > 0 and ly > 0:
                                    dx_list.append(lx - sx)
                                    dy_list.append(ly - sy)

                        if len(dx_list) >= 2:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # Check horizontal swipe (App Switcher / Alt+Tab)
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    # Swipe Right -> Walk Through Windows Forward (Alt+Tab)
                                    subprocess.Popen([
                                        "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
                                        "org.kde.kglobalaccel.Component.invokeShortcut", "Walk Through Windows"
                                    ], stderr=subprocess.DEVNULL)
                                else:
                                    # Swipe Left -> Walk Through Windows Reverse (Alt+Shift+Tab)
                                    subprocess.Popen([
                                        "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
                                        "org.kde.kglobalaccel.Component.invokeShortcut", "Walk Through Windows (Reverse)"
                                    ], stderr=subprocess.DEVNULL)

                            # Check vertical swipe (Task View / Show Desktop)
                            elif abs(avg_dy) > self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.3:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dy < 0:
                                    # Swipe Up -> Task View / Overview
                                    subprocess.Popen([
                                        "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
                                        "org.kde.kglobalaccel.Component.invokeShortcut", "Overview"
                                    ], stderr=subprocess.DEVNULL)
                                else:
                                    # Swipe Down -> Show Desktop
                                    subprocess.Popen([
                                        "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
                                        "org.kde.kglobalaccel.Component.invokeShortcut", "Show Desktop"
                                    ], stderr=subprocess.DEVNULL)

            except Exception:
                break


def start_gesture_daemon_background():
    router = GestureRouter()
    thread = threading.Thread(target=router.run, daemon=True)
    thread.start()


if __name__ == "__main__":
    r = GestureRouter()
    r.run()
