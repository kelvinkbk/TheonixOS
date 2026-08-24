#!/usr/bin/env python3
"""
Theonix Gesture Router Daemon — Centroid-based Multi-Touch Gestures for Touchpads.
Provides bidirectional 3-finger swipe UP (Open Task View) and swipe DOWN (Close Task View / Show Desktop).
"""

import os
import glob
import select
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

BTN_TOOL_FINGER = 0x145
BTN_TOOL_DOUBLETAP = 0x14d
BTN_TOOL_TRIPLETAP = 0x14e
BTN_TOOL_QUADTAP = 0x14f


def is_overview_open() -> bool:
    try:
        res = subprocess.run([
            "qdbus6", "org.kde.KWin", "/Effects",
            "org.freedesktop.DBus.Properties.Get", "org.kde.kwin.Effects", "activeEffects"
        ], capture_output=True, text=True, timeout=0.15)
        text = res.stdout.lower()
        return "overview" in text or "desktopgrid" in text
    except Exception:
        return False


class TouchpadRouter:
    def __init__(self, dev_path: str):
        self.dev_path = dev_path
        self.fd = None
        self.slots = {}
        self.btn_triple = False
        self.btn_quad = False
        self.start_centroid = None
        self.gesture_done = False
        self.touch_start_time = 0
        self.last_action_time = 0
        self.threshold = 85  # Ultra-responsive sensitivity (85px)

    def open(self):
        try:
            self.fd = os.open(self.dev_path, os.O_RDONLY | os.O_NONBLOCK)
            return True
        except Exception:
            return False

    def trigger(self, shortcut: str):
        now = time.time()
        if now - self.last_action_time < 0.32:
            return
        self.last_action_time = now
        self.gesture_done = True
        subprocess.Popen([
            "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def process(self):
        current_slot = 0
        now = time.time()

        try:
            while True:
                data = os.read(self.fd, EVENT_SIZE)
                if not data or len(data) < EVENT_SIZE:
                    break
                sec, usec, ev_type, ev_code, ev_val = struct.unpack(EVENT_FORMAT, data)

                if ev_type == EV_KEY:
                    if ev_code == BTN_TOOL_TRIPLETAP:
                        self.btn_triple = (ev_val == 1)
                        if ev_val == 0:
                            self.start_centroid = None
                            self.gesture_done = False
                    elif ev_code == BTN_TOOL_QUADTAP:
                        self.btn_quad = (ev_val == 1)
                        if ev_val == 0:
                            self.start_centroid = None
                            self.gesture_done = False
                    elif ev_code == BTN_TOOL_FINGER and ev_val == 0:
                        self.slots.clear()
                        self.start_centroid = None
                        self.gesture_done = False
                        self.btn_triple = False
                        self.btn_quad = False

                elif ev_type == EV_ABS:
                    if ev_code == ABS_MT_SLOT:
                        current_slot = ev_val
                    elif ev_code == ABS_MT_TRACKING_ID:
                        if ev_val == -1:
                            self.slots.pop(current_slot, None)
                            if not self.slots:
                                self.start_centroid = None
                                self.gesture_done = False
                                self.btn_triple = False
                                self.btn_quad = False
                        else:
                            if current_slot not in self.slots:
                                self.slots[current_slot] = [0, 0]
                    elif ev_code == ABS_MT_POSITION_X:
                        if current_slot in self.slots:
                            self.slots[current_slot][0] = ev_val
                    elif ev_code == ABS_MT_POSITION_Y:
                        if current_slot in self.slots:
                            self.slots[current_slot][1] = ev_val

                elif ev_type == EV_SYN and ev_code == 0:
                    active_count = len(self.slots)
                    is_3_fingers = self.btn_triple or active_count == 3
                    is_4_fingers = self.btn_quad or active_count >= 4

                    if (is_3_fingers or is_4_fingers) and not self.gesture_done:
                        valid_coords = [c for c in self.slots.values() if c[0] > 0 and c[1] > 0]
                        if valid_coords:
                            cx = sum(c[0] for c in valid_coords) / len(valid_coords)
                            cy = sum(c[1] for c in valid_coords) / len(valid_coords)

                            if self.start_centroid is None:
                                self.start_centroid = (cx, cy)
                                self.touch_start_time = now
                            else:
                                sx, sy = self.start_centroid
                                dx = cx - sx
                                dy = cy - sy

                                # --- 3-FINGER GESTURES ---
                                if is_3_fingers and not is_4_fingers:
                                    # Horizontal swipe -> App switcher (Alt+Tab)
                                    if abs(dx) > self.threshold and abs(dx) > abs(dy) * 1.1:
                                        if dx > 0:
                                            self.trigger("Walk Through Windows")
                                        else:
                                            self.trigger("Walk Through Windows (Reverse)")

                                    # Vertical swipe UP -> Open Task View / Overview
                                    elif dy < -self.threshold and abs(dy) > abs(dx) * 1.1:
                                        if not is_overview_open():
                                            self.trigger("Overview")

                                    # Vertical swipe DOWN -> If in Overview: Close Overview! Else: Show Desktop!
                                    elif dy > self.threshold and abs(dy) > abs(dx) * 1.1:
                                        if is_overview_open():
                                            self.trigger("Overview")  # Exits Overview back to active windows
                                        else:
                                            self.trigger("Show Desktop")

                                # --- 4-FINGER GESTURES ---
                                elif is_4_fingers:
                                    # Horizontal swipe -> Switch Virtual Desktops
                                    if abs(dx) > self.threshold and abs(dx) > abs(dy) * 1.1:
                                        if dx > 0:
                                            self.trigger("Switch One Desktop to the Right")
                                        else:
                                            self.trigger("Switch One Desktop to the Left")

                                    # Vertical swipe UP -> Workspaces Grid View
                                    elif dy < -self.threshold and abs(dy) > abs(dx) * 1.1:
                                        self.trigger("Grid View")

                                    # Vertical swipe DOWN -> If in Grid: Close Grid!
                                    elif dy > self.threshold and abs(dy) > abs(dx) * 1.1:
                                        if is_overview_open():
                                            self.trigger("Grid View")
                                        else:
                                            self.trigger("Show Desktop")

        except BlockingIOError:
            pass
        except Exception:
            pass


def main():
    routers = []
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            num = os.path.basename(path).replace("event", "")
            name_file = f"/sys/class/input/event{num}/device/name"
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    name = f.read().lower().strip()
                    if "touchpad" in name or "elan" in name or "synaptics" in name:
                        r = TouchpadRouter(path)
                        if r.open():
                            routers.append(r)
        except Exception:
            pass

    if not routers:
        sys.exit(1)

    fd_map = {r.fd: r for r in routers}

    while True:
        try:
            readable, _, _ = select.select(list(fd_map.keys()), [], [], 1.0)
            for fd in readable:
                if fd in fd_map:
                    fd_map[fd].process()
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(0.1)


if __name__ == "__main__":
    main()
