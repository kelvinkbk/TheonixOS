#!/usr/bin/env python3
"""
Theonix Gesture Daemon — Multi-Device Precision Multi-Touch Gesture Router.
Listens to all active touchpad devices in parallel with high sensitivity.
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

BTN_TOOL_DOUBLETAP = 0x14d
BTN_TOOL_TRIPLETAP = 0x14e
BTN_TOOL_QUADTAP = 0x14f


class TouchpadTracker:
    def __init__(self, dev_path: str, name: str):
        self.dev_path = dev_path
        self.name = name
        self.fd = None
        self.active_slots = {}
        self.start_positions = {}
        self.last_positions = {}
        self.start_times = {}
        self.max_fingers = 0
        self.gesture_triggered = False
        self.min_swipe_distance = 60  # Ultra-responsive threshold (60px)
        self.tap_max_distance = 40    # Max movement for tap
        self.tap_max_duration = 0.35  # Max duration for tap
        self.cooldown = 0.25          # Seconds
        self.last_trigger_time = 0

    def open(self):
        try:
            self.fd = os.open(self.dev_path, os.O_RDONLY | os.O_NONBLOCK)
            return True
        except Exception:
            return False

    def invoke_kwin(self, shortcut: str):
        subprocess.Popen([
            "qdbus6", "org.kde.kglobalaccel", "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut", shortcut
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def process_events(self):
        current_slot = 0
        now = time.time()

        try:
            while True:
                data = os.read(self.fd, EVENT_SIZE)
                if not data or len(data) < EVENT_SIZE:
                    break
                sec, usec, ev_type, ev_code, ev_val = struct.unpack(EVENT_FORMAT, data)

                if ev_type == EV_KEY:
                    # Key tracking for tap / finger count fallback
                    if ev_code == BTN_TOOL_TRIPLETAP and ev_val == 1:
                        self.max_fingers = max(self.max_fingers, 3)
                    elif ev_code == BTN_TOOL_QUADTAP and ev_val == 1:
                        self.max_fingers = max(self.max_fingers, 4)

                elif ev_type == EV_ABS:
                    if ev_code == ABS_MT_SLOT:
                        current_slot = ev_val
                    elif ev_code == ABS_MT_TRACKING_ID:
                        if ev_val == -1:
                            # Finger lifted
                            self.active_slots.pop(current_slot, None)
                            if len(self.active_slots) == 0:
                                # All fingers lifted -> Check Taps
                                if not self.gesture_triggered:
                                    t_durations = [now - t for t in self.start_times.values()]
                                    if t_durations and max(t_durations) < self.tap_max_duration:
                                        max_dist = 0
                                        for s in self.start_positions:
                                            if s in self.last_positions:
                                                sx, sy = self.start_positions[s]
                                                lx, ly = self.last_positions[s]
                                                dist = ((lx - sx) ** 2 + (ly - sy) ** 2) ** 0.5
                                                max_dist = max(max_dist, dist)

                                        if max_dist < self.tap_max_distance:
                                            if self.max_fingers == 3:
                                                self.invoke_kwin("Overview")
                                            elif self.max_fingers >= 4:
                                                self.invoke_kwin("Grid View")

                                # Reset state
                                self.start_positions.clear()
                                self.last_positions.clear()
                                self.start_times.clear()
                                self.max_fingers = 0
                                self.gesture_triggered = False
                        else:
                            # Finger touched down
                            self.active_slots[current_slot] = ev_val
                            self.start_times[current_slot] = now
                            self.max_fingers = max(self.max_fingers, len(self.active_slots))

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
                    finger_count = max(len(self.active_slots), self.max_fingers)

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
                        if (finger_count == 3 or len(dx_list) >= 2) and dx_list:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # 3-Finger Horizontal Swipe -> App Switcher (Alt+Tab)
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.1:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self.invoke_kwin("Walk Through Windows")
                                else:
                                    self.invoke_kwin("Walk Through Windows (Reverse)")

                            # 3-Finger Vertical Swipe UP -> Task View / Overview
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.1:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self.invoke_kwin("Overview")

                            # 3-Finger Vertical Swipe DOWN -> Show Desktop
                            elif avg_dy > self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.1:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self.invoke_kwin("Show Desktop")

                        # --- 4-FINGER GESTURES ---
                        elif finger_count >= 4 and len(dx_list) >= 2:
                            avg_dx = sum(dx_list) / len(dx_list)
                            avg_dy = sum(dy_list) / len(dy_list)

                            # 4-Finger Horizontal Swipe -> Switch Virtual Desktops
                            if abs(avg_dx) > self.min_swipe_distance and abs(avg_dx) > abs(avg_dy) * 1.1:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                if avg_dx > 0:
                                    self.invoke_kwin("Switch One Desktop to the Right")
                                else:
                                    self.invoke_kwin("Switch One Desktop to the Left")

                            # 4-Finger Vertical Swipe UP -> Workspaces Grid View
                            elif avg_dy < -self.min_swipe_distance and abs(avg_dy) > abs(avg_dx) * 1.1:
                                self.gesture_triggered = True
                                self.last_trigger_time = now
                                self.invoke_kwin("Grid View")

        except BlockingIOError:
            pass
        except Exception:
            pass


def main():
    trackers = []
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            num = os.path.basename(path).replace("event", "")
            name_file = f"/sys/class/input/event{num}/device/name"
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    name = f.read().lower().strip()
                    if "touchpad" in name or "elan" in name or "synaptics" in name:
                        t = TouchpadTracker(path, name)
                        if t.open():
                            trackers.append(t)
        except Exception:
            pass

    if not trackers:
        sys.exit(1)

    fd_map = {t.fd: t for t in trackers}

    while True:
        try:
            readable, _, _ = select.select(list(fd_map.keys()), [], [], 1.0)
            for fd in readable:
                if fd in fd_map:
                    fd_map[fd].process_events()
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(0.1)


if __name__ == "__main__":
    main()
