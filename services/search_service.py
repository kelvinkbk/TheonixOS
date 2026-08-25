#!/usr/bin/env python3
"""
Theonix OS — Global Omni-Search Service (org.theonix.Search)
Provides unified desktop search across Applications, Files, Settings, Bookmarks, and System Actions.
Includes interactive Spotlight-style floating glass overlay triggered via D-Bus / hotkey (Ctrl+Space).
"""

import sys
import os
import glob
import json
import sqlite3
import subprocess
import threading
from typing import Dict, Any, List

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QKeyEvent
from PyQt6.QtDBus import QDBusConnection


class SearchEngine:
    """Fast in-memory indexer for system applications, settings, files, and actions."""

    def __init__(self):
        self._apps: List[Dict[str, Any]] = []
        self._settings: List[Dict[str, Any]] = []
        self._system_actions: List[Dict[str, Any]] = []
        self.reindex()

    def reindex(self):
        self._index_apps()
        self._index_settings()
        self._index_actions()

    def _index_apps(self):
        self._apps.clear()
        desktop_dirs = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications"),
            "/var/lib/flatpak/exports/share/applications"
        ]
        seen_names = set()

        for d in desktop_dirs:
            if not os.path.exists(d):
                continue
            for f in glob.glob(os.path.join(d, "*.desktop")):
                try:
                    name, exec_cmd, icon, comment = "", "", "application-x-executable", ""
                    with open(f, "r", encoding="utf-8", errors="ignore") as file:
                        for line in file:
                            line = line.strip()
                            if line.startswith("Name=") and not name:
                                name = line[5:].strip()
                            elif line.startswith("Exec=") and not exec_cmd:
                                exec_cmd = line[5:].strip().split("%")[0].strip()
                            elif line.startswith("Icon=") and icon == "application-x-executable":
                                icon = line[5:].strip()
                            elif line.startswith("Comment=") and not comment:
                                comment = line[8:].strip()

                    if name and exec_cmd and name.lower() not in seen_names:
                        seen_names.add(name.lower())
                        self._apps.append({
                            "id": f"app:{name}",
                            "title": name,
                            "subtitle": comment or f"Application ({exec_cmd.split()[0]})",
                            "category": "Application",
                            "icon": icon,
                            "exec": exec_cmd
                        })
                except Exception:
                    pass

    def _index_settings(self):
        self._settings = [
            {"id": "setting:system", "title": "System & About", "subtitle": "Hardware specs, kernel info, and OS release", "category": "Settings", "icon": "preferences-system", "exec": "theonix-settings"},
            {"id": "setting:ai", "title": "AI & THAID Engine", "subtitle": "Ollama models, GPU acceleration, and inference settings", "category": "Settings", "icon": "preferences-system", "exec": "theonix-settings"},
            {"id": "setting:gestures", "title": "Touchpad & Gestures", "subtitle": "Touchpad sensitivities, 3-finger and 4-finger swipes", "category": "Settings", "icon": "input-touchpad", "exec": "theonix-settings"},
            {"id": "setting:voice", "title": "Voice Assistant & Wake Word", "subtitle": "Hey Theonix wake word, Whisper STT, and Piper voice models", "category": "Settings", "icon": "audio-input-microphone", "exec": "theonix-settings"},
            {"id": "setting:display", "title": "Display & Scaling", "subtitle": "Resolution, refresh rate, scaling factor, and night light", "category": "Settings", "icon": "video-display", "exec": "theonix-settings"},
            {"id": "setting:network", "title": "Network & Wi-Fi", "subtitle": "Wireless connections, IP configuration, and DNS", "category": "Settings", "icon": "network-wireless", "exec": "theonix-settings"},
            {"id": "setting:audio", "title": "Sound & Audio", "subtitle": "PipeWire volume, output sinks, and input sources", "category": "Settings", "icon": "audio-speakers", "exec": "theonix-settings"},
            {"id": "setting:updates", "title": "Software & System Updates", "subtitle": "Arch native, Flatpak, and Theonix updates", "category": "Settings", "icon": "system-software-update", "exec": "theonix-settings"},
            {"id": "setting:storage", "title": "Storage & Snapshots", "subtitle": "Btrfs snapshots, partition storage, and disk health", "category": "Settings", "icon": "drive-harddisk", "exec": "theonix-settings"},
        ]

    def _index_actions(self):
        self._system_actions = [
            {"id": "action:lock", "title": "Lock Screen", "subtitle": "Secure current user session", "category": "Action", "icon": "system-lock-screen", "exec": "loginctl lock-session"},
            {"id": "action:screenshot", "title": "Take Screenshot", "subtitle": "Capture display or active window", "category": "Action", "icon": "spectacle", "exec": "spectacle -b"},
            {"id": "action:mute", "title": "Mute / Unmute Audio", "subtitle": "Toggle master audio output sink", "category": "Action", "icon": "audio-volume-muted", "exec": "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"},
            {"id": "action:terminal", "title": "Open Terminal", "subtitle": "Launch Konsole terminal emulator", "category": "Action", "icon": "utilities-terminal", "exec": "konsole"},
            {"id": "action:restart", "title": "Restart System", "subtitle": "Reboot Theonix OS safely", "category": "Action", "icon": "system-reboot", "exec": "systemctl reboot"},
            {"id": "action:shutdown", "title": "Power Off System", "subtitle": "Shut down computer", "category": "Action", "icon": "system-shutdown", "exec": "systemctl poweroff"},
        ]

    def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            # Default recommendations: Settings, popular apps, and quick actions
            return (self._settings[:3] + self._apps[:3] + self._system_actions[:2])[:limit]

        results = []

        # 1. Search Actions
        for act in self._system_actions:
            if q in act["title"].lower() or q in act["subtitle"].lower():
                results.append(act)

        # 2. Search Settings
        for stg in self._settings:
            if q in stg["title"].lower() or q in stg["subtitle"].lower():
                results.append(stg)

        # 3. Search Apps
        for app in self._apps:
            if q in app["title"].lower() or q in app["subtitle"].lower():
                results.append(app)

        # 4. Search Common Files
        user_dirs = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Projects")
        ]
        for u_dir in user_dirs:
            if not os.path.exists(u_dir):
                continue
            for root, dirs, files in os.walk(u_dir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
                for f in files:
                    if q in f.lower():
                        full_path = os.path.join(root, f)
                        results.append({
                            "id": f"file:{full_path}",
                            "title": f,
                            "subtitle": full_path,
                            "category": "File",
                            "icon": "text-plain",
                            "exec": f"xdg-open '{full_path}'"
                        })
                        if len(results) >= limit * 2:
                            break
                if len(results) >= limit * 2:
                    break

        return results[:limit]


class GlassSpotlightOverlay(QWidget):
    """Modern centered spotlight search modal overlay."""

    def __init__(self, search_engine: SearchEngine):
        super().__init__()
        self.engine = search_engine
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 480)

        # Position Center of primary display
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 3)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Container
        self.container = QWidget(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: #f2060913;
                border: 1.5px solid #00FFAA;
                border-radius: 20px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Inter', sans-serif;
            }
        """)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        # Search Bar Row
        s_row = QHBoxLayout()
        icon_lbl = QLabel("🔍")
        icon_lbl.setFont(QFont("Inter", 16))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search apps, files, settings, actions, or ask THAID...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 16px;
                font-family: 'Inter', sans-serif;
                padding: 4px;
            }
        """)
        self.input_field.textChanged.connect(self._on_text_changed)
        
        s_row.addWidget(icon_lbl)
        s_row.addWidget(self.input_field)
        c_layout.addLayout(s_row)

        # Separator line
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255, 255, 255, 0.1);")
        c_layout.addWidget(sep)

        # Results List
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 10px;
                padding: 8px 12px;
                color: #FFFFFF;
                margin-bottom: 4px;
            }
            QListWidget::item:selected, QListWidget::item:hover {
                background: rgba(0, 255, 170, 0.15);
                border: 1px solid rgba(0, 255, 170, 0.4);
            }
        """)
        self.results_list.itemClicked.connect(self._on_item_clicked)
        c_layout.addWidget(self.results_list)

        # Footer
        footer_row = QHBoxLayout()
        f_info = QLabel("<b>↑↓</b> to navigate &nbsp;•&nbsp; <b>Enter</b> to launch &nbsp;•&nbsp; <b>Esc</b> to close")
        f_info.setStyleSheet("color: #64748B; font-size: 11px;")
        
        thaid_tag = QLabel("⚡ Theonix Omni-Search")
        thaid_tag.setStyleSheet("color: #00FFAA; font-size: 11px; font-weight: bold;")

        footer_row.addWidget(f_info)
        footer_row.addStretch()
        footer_row.addWidget(thaid_tag)
        c_layout.addLayout(footer_row)

        layout.addWidget(self.container)
        self._on_text_changed("")

    def _on_text_changed(self, text: str):
        results = self.engine.search(text, limit=6)
        self.results_list.clear()
        self._current_results = results

        for r in results:
            item = QListWidgetItem()
            cat_badge = f"[{r['category']}]"
            item.setText(f"{r['title']}   {cat_badge}\n{r['subtitle']}")
            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_item_clicked(self, item):
        row = self.results_list.row(item)
        if 0 <= row < len(self._current_results):
            entry = self._current_results[row]
            self._launch_entry(entry)

    def _launch_entry(self, entry: Dict[str, Any]):
        cmd = entry.get("exec", "")
        if cmd:
            subprocess.Popen(cmd, shell=True)
        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            row = self.results_list.currentRow()
            if 0 <= row < len(self._current_results):
                self._launch_entry(self._current_results[row])
        elif event.key() == Qt.Key.Key_Down:
            curr = self.results_list.currentRow()
            if curr < self.results_list.count() - 1:
                self.results_list.setCurrentRow(curr + 1)
        elif event.key() == Qt.Key.Key_Up:
            curr = self.results_list.currentRow()
            if curr > 0:
                self.results_list.setCurrentRow(curr - 1)
        else:
            super().keyPressEvent(event)


class SearchService(QObject):
    searchExecuted = pyqtSignal(str, str)  # query, selected_id

    def __init__(self):
        super().__init__()
        self.engine = SearchEngine()
        self.overlay: GlassSpotlightOverlay = None

    def set_overlay(self, overlay: GlassSpotlightOverlay):
        self.overlay = overlay

    @pyqtSlot(str, int, result=str)
    def Query(self, query: str, limit: int = 8) -> str:
        """Searches across apps, files, settings, and actions, returning JSON list."""
        results = self.engine.search(query, limit)
        return json.dumps(results)

    @pyqtSlot()
    def Toggle(self):
        """Toggles the visibility of the Spotlight search overlay."""
        if self.overlay:
            if self.overlay.isVisible():
                self.overlay.hide()
            else:
                self.overlay.show()
                self.overlay.raise_()
                self.overlay.activateWindow()
                self.overlay.input_field.setFocus()
                self.overlay.input_field.selectAll()

    @pyqtSlot()
    def Show(self):
        if self.overlay:
            self.overlay.show()
            self.overlay.raise_()
            self.overlay.activateWindow()
            self.overlay.input_field.setFocus()

    @pyqtSlot()
    def Hide(self):
        if self.overlay:
            self.overlay.hide()

    @pyqtSlot(str, result=bool)
    def Launch(self, target_id: str) -> bool:
        """Launches a specific item by its unique ID."""
        for collection in [self.engine._apps, self.engine._settings, self.engine._system_actions]:
            for item in collection:
                if item.get("id") == target_id:
                    cmd = item.get("exec", "")
                    if cmd:
                        subprocess.Popen(cmd, shell=True)
                        self.searchExecuted.emit(target_id, cmd)
                        return True
        return False

    @pyqtSlot()
    def Reindex(self):
        threading.Thread(target=self.engine.reindex, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    service = SearchService()
    overlay = GlassSpotlightOverlay(service.engine)
    service.set_overlay(overlay)

    if not bus.registerService("org.theonix.Search"):
        print("[SearchService] Failed to register D-Bus service 'org.theonix.Search'")
        sys.exit(1)

    if not bus.registerObject("/org/theonix/Search", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[SearchService] Failed to register D-Bus object at '/org/theonix/Search'")
        sys.exit(1)

    print("[SearchService] Theonix Search Service active on org.theonix.Search [/org/theonix/Search]")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
