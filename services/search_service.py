#!/usr/bin/env python3
"""
Theonix OS — Global Omni-Search & Spotlight Service (org.theonix.Search)
Next-Gen Unified Desktop Search across:
- Applications (.desktop files)
- Browser History & Bookmarks (~/.config/theonix/browser/*.db)
- Recent Files (~/.local/share/recently-used.xbel + user workspaces)
- Theonix Settings Deep-Links (11 settings sub-pages)
- Instant Math & Calculator Evaluator
- THAID AI Assistant Prompter
- System Actions (Lock, Screenshot, Terminal, Mute, Reboot)

Includes modern centered Glass Spotlight modal overlay triggered via Ctrl+Space / D-Bus.
"""

import sys
import os
import glob
import json
import math
import re
import sqlite3
import subprocess
import threading
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
if not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QFrame
)
from PyQt6.QtCore import Qt, QObject, pyqtSlot, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QCursor
from PyQt6.QtDBus import QDBusConnection


# =============================================================================
# MULTI-SOURCE SEARCH ENGINE
# =============================================================================

class SearchEngine:
    """Fast multi-source in-memory & SQLite indexer."""

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
                            "badge_color": "#A855F7",
                            "icon": icon,
                            "exec": exec_cmd
                        })
                except Exception:
                    pass

    def _index_settings(self):
        self._settings = [
            {"id": "setting:system", "title": "System & About", "subtitle": "Hardware specs, kernel info, and OS release", "category": "Settings", "badge_color": "#00FFAA", "icon": "preferences-system", "exec": "theonix-settings --page system"},
            {"id": "setting:ai", "title": "AI & THAID Engine", "subtitle": "Ollama models, GPU acceleration, and inference settings", "category": "Settings", "badge_color": "#00FFAA", "icon": "preferences-system", "exec": "theonix-settings --page ai"},
            {"id": "setting:appearance", "title": "Appearance & Theme", "subtitle": "Dark/Light themes, Cyber-Obsidian accents, wallpapers", "category": "Settings", "badge_color": "#00FFAA", "icon": "preferences-desktop-theme", "exec": "theonix-settings --page appearance"},
            {"id": "setting:display", "title": "Display & Scaling", "subtitle": "Resolution, refresh rate (144Hz), scaling, night light", "category": "Settings", "badge_color": "#00FFAA", "icon": "video-display", "exec": "theonix-settings --page display"},
            {"id": "setting:gestures", "title": "Touchpad & Gestures", "subtitle": "Touchpad sensitivities, 3-finger and 4-finger swipes", "category": "Settings", "badge_color": "#00FFAA", "icon": "input-touchpad", "exec": "theonix-settings --page gestures"},
            {"id": "setting:voice", "title": "Voice Assistant & Wake Word", "subtitle": "Hey Theonix wake word, Whisper STT, and Piper voices", "category": "Settings", "badge_color": "#00FFAA", "icon": "audio-input-microphone", "exec": "theonix-settings --page voice"},
            {"id": "setting:network", "title": "Network & Wi-Fi", "subtitle": "Wireless connections, IP configuration, and DNS", "category": "Settings", "badge_color": "#00FFAA", "icon": "network-wireless", "exec": "theonix-settings --page network"},
            {"id": "setting:audio", "title": "Sound & Audio", "subtitle": "PipeWire volume, output sinks, and input sources", "category": "Settings", "badge_color": "#00FFAA", "icon": "audio-speakers", "exec": "theonix-settings --page audio"},
            {"id": "setting:storage", "title": "Storage & Snapshots", "subtitle": "Btrfs snapshots, NVMe partition storage, disk health", "category": "Settings", "badge_color": "#00FFAA", "icon": "drive-harddisk", "exec": "theonix-settings --page storage"},
            {"id": "setting:advanced", "title": "Advanced & Developer", "subtitle": "Passkeys, system logs, UACL permissions, kernel tuning", "category": "Settings", "badge_color": "#00FFAA", "icon": "utilities-terminal", "exec": "theonix-settings --page advanced"},
            {"id": "setting:updates", "title": "Software & Updates", "subtitle": "Pacman rolling updates, Flatpak apps, Theonix core", "category": "Settings", "badge_color": "#00FFAA", "icon": "system-software-update", "exec": "theonix-settings --page updates"},
        ]

    def _index_actions(self):
        self._system_actions = [
            {"id": "action:lock", "title": "Lock Screen", "subtitle": "Secure current user session", "category": "Action", "badge_color": "#38BDF8", "icon": "system-lock-screen", "exec": "loginctl lock-session"},
            {"id": "action:screenshot", "title": "Take Screenshot", "subtitle": "Capture display or active window", "category": "Action", "badge_color": "#38BDF8", "icon": "spectacle", "exec": "spectacle -b"},
            {"id": "action:mute", "title": "Mute / Unmute Audio", "subtitle": "Toggle master audio output sink", "category": "Action", "badge_color": "#38BDF8", "icon": "audio-volume-muted", "exec": "pactl set-sink-mute @DEFAULT_SINK@ toggle"},
            {"id": "action:terminal", "title": "Open Terminal", "subtitle": "Launch interactive shell", "category": "Action", "badge_color": "#38BDF8", "icon": "utilities-terminal", "exec": "konsole"},
            {"id": "action:restart", "title": "Restart System", "subtitle": "Reboot Theonix OS safely", "category": "Action", "badge_color": "#EF4444", "icon": "system-reboot", "exec": "systemctl reboot"},
            {"id": "action:shutdown", "title": "Power Off System", "subtitle": "Shut down computer", "category": "Action", "badge_color": "#EF4444", "icon": "system-shutdown", "exec": "systemctl poweroff"},
        ]

    def _query_browser_history(self, q: str, limit: int = 4) -> List[Dict[str, Any]]:
        results = []
        db_path = os.path.expanduser("~/.config/theonix/browser/history.db")
        if not os.path.exists(db_path):
            return results

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("""
                SELECT title, url FROM history 
                WHERE title LIKE ? OR url LIKE ? 
                ORDER BY last_visited DESC LIMIT ?
            """, (f"%{q}%", f"%{q}%", limit))
            for row in cur.fetchall():
                title, url = row[0] or url, row[1]
                results.append({
                    "id": f"history:{url}",
                    "title": title,
                    "subtitle": url,
                    "category": "Web History",
                    "badge_color": "#00D4FF",
                    "icon": "globe",
                    "exec": f"theonix-browser '{url}'"
                })
            conn.close()
        except Exception:
            pass
        return results

    def _query_browser_bookmarks(self, q: str, limit: int = 3) -> List[Dict[str, Any]]:
        results = []
        db_path = os.path.expanduser("~/.config/theonix/browser/bookmarks.db")
        if not os.path.exists(db_path):
            return results

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("""
                SELECT title, url FROM bookmarks 
                WHERE title LIKE ? OR url LIKE ? 
                LIMIT ?
            """, (f"%{q}%", f"%{q}%", limit))
            for row in cur.fetchall():
                title, url = row[0] or url, row[1]
                results.append({
                    "id": f"bookmark:{url}",
                    "title": title,
                    "subtitle": f"Bookmark • {url}",
                    "category": "Bookmark",
                    "badge_color": "#F59E0B",
                    "icon": "bookmark",
                    "exec": f"theonix-browser '{url}'"
                })
            conn.close()
        except Exception:
            pass
        return results

    def _query_recent_files(self, q: str, limit: int = 4) -> List[Dict[str, Any]]:
        results = []
        xbel_path = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(xbel_path):
            try:
                tree = ET.parse(xbel_path)
                root = tree.getroot()
                for bookmark in reversed(root.findall(".//bookmark")):
                    href = bookmark.attrib.get("href", "")
                    if href.startswith("file://"):
                        fpath = href[7:]
                        fname = os.path.basename(fpath)
                        if q in fname.lower() or q in fpath.lower():
                            results.append({
                                "id": f"recent:{fpath}",
                                "title": fname,
                                "subtitle": fpath,
                                "category": "Recent File",
                                "badge_color": "#38BDF8",
                                "icon": "document-open",
                                "exec": f"xdg-open '{fpath}'"
                            })
                            if len(results) >= limit:
                                break
            except Exception:
                pass

        if len(results) < limit:
            # Fallback file scanner in user workspace
            user_dirs = [
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Projects")
            ]
            for u_dir in user_dirs:
                if not os.path.exists(u_dir):
                    continue
                for root_dir, dirs, files in os.walk(u_dir):
                    dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != ".git"]
                    for f in files:
                        if q in f.lower():
                            full_path = os.path.join(root_dir, f)
                            results.append({
                                "id": f"file:{full_path}",
                                "title": f,
                                "subtitle": full_path,
                                "category": "File",
                                "badge_color": "#38BDF8",
                                "icon": "text-plain",
                                "exec": f"xdg-open '{full_path}'"
                            })
                            if len(results) >= limit:
                                break
                    if len(results) >= limit:
                        break

        return results[:limit]

    def _eval_calculator(self, query: str) -> Dict[str, Any]:
        """Safely evaluates mathematical expressions."""
        clean = query.strip()
        # Check if contains numbers and arithmetic operators
        if re.search(r"^[0-9\.\s\+\-\*\/\^\(\)\%\,]+$", clean) and any(c in clean for c in "+-*/^%"):
            try:
                expr = clean.replace("^", "**").replace("%", "/100")
                # Allowed safe globals
                safe_dict = {
                    "math": math, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
                    "tan": math.tan, "log": math.log, "pi": math.pi, "e": math.e,
                    "pow": math.pow, "abs": abs, "round": round
                }
                res = eval(expr, {"__builtins__": {}}, safe_dict)
                if isinstance(res, (int, float)):
                    fmt_res = f"{res:g}" if isinstance(res, float) else str(res)
                    return {
                        "id": f"calc:{fmt_res}",
                        "title": f"= {fmt_res}",
                        "subtitle": f"Calculation result for '{clean}' (Press Enter to copy)",
                        "category": "Calculator",
                        "badge_color": "#F43F5E",
                        "icon": "accessories-calculator",
                        "exec": f"echo -n '{fmt_res}' | xclip -selection clipboard 2>/dev/null || wl-copy '{fmt_res}'"
                    }
            except Exception:
                pass
        return None

    def search(self, query: str, limit: int = 9) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            # Default recommendations: Settings, Apps, Actions
            return (self._settings[:3] + self._apps[:3] + self._system_actions[:3])[:limit]

        results = []

        # 1. Calculator Check
        calc_item = self._eval_calculator(query)
        if calc_item:
            results.append(calc_item)

        # 2. Search Settings
        for stg in self._settings:
            if q in stg["title"].lower() or q in stg["subtitle"].lower():
                results.append(stg)

        # 3. Search Apps
        for app in self._apps:
            if q in app["title"].lower() or q in app["subtitle"].lower():
                results.append(app)

        # 4. Search Browser History & Bookmarks
        results.extend(self._query_browser_history(q, limit=3))
        results.extend(self._query_browser_bookmarks(q, limit=2))

        # 5. Search Recent Files
        results.extend(self._query_recent_files(q, limit=3))

        # 6. Search System Actions
        for act in self._system_actions:
            if q in act["title"].lower() or q in act["subtitle"].lower():
                results.append(act)

        # 7. Always include THAID AI Option if query has content
        if len(q) >= 2:
            clean_query = query.strip().lstrip("?").strip()
            results.append({
                "id": f"thaid:{clean_query}",
                "title": f"Ask THAID: \"{clean_query}\"",
                "subtitle": "Dispatch task / prompt to Local AI Assistant",
                "category": "THAID AI",
                "badge_color": "#C084FC",
                "icon": "system-help",
                "exec": f"qdbus6 org.theonix.AIGUI /org/theonix/AIGUI toggleListening"
            })

        return results[:limit]


# =============================================================================
# REFINED GLASS SPOTLIGHT MODAL OVERLAY
# =============================================================================

class GlassSpotlightOverlay(QWidget):
    """Modern centered spotlight search modal overlay with rich category badges."""

    def __init__(self, search_engine: SearchEngine):
        super().__init__()
        self.engine = search_engine
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(640, 520)

        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 3)

        self._init_ui()
        self._load_results("")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Main Container Frame
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(22, 28, 38, 0.98), stop:1 rgba(11, 15, 22, 0.99));
                border: 1.5px solid #333C49;
                border-radius: 22px;
            }
            QLabel {
                color: #F4F7FB;
                font-family: 'Inter', sans-serif;
            }
        """)

        # Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 16)
        self.container.setGraphicsEffect(shadow)

        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        # Search Bar Row
        s_row = QHBoxLayout()
        s_row.setSpacing(10)
        
        icon_lbl = QLabel("🔍")
        icon_lbl.setFont(QFont("Inter", 16))
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Search apps, web history, files, settings, or calculate...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #F4F7FB;
                font-size: 16px;
                font-family: 'Inter', sans-serif;
                font-weight: 500;
                padding: 4px;
            }
            QLineEdit:focus { border: none; }
        """)
        self.input_field.textChanged.connect(self._on_text_changed)

        s_row.addWidget(icon_lbl)
        s_row.addWidget(self.input_field)
        c_layout.addLayout(s_row)

        # Divider
        div = QFrame()
        div.setStyleSheet("background: #333C49; min-height: 1px; max-height: 1px;")
        c_layout.addWidget(div)

        # Results List Widget
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: #1C2330;
                border: 1px solid #2B3545;
                border-radius: 12px;
                margin-bottom: 6px;
                padding: 6px 10px;
                color: #F4F7FB;
            }
            QListWidget::item:hover {
                background: #252F40;
                border-color: #4B5970;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(123,97,255,0.35), stop:1 rgba(18,216,197,0.12));
                border: 1px solid #7B61FF;
            }
        """)
        self.results_list.itemClicked.connect(self._on_item_activated)
        c_layout.addWidget(self.results_list)

        # Footer Status
        f_row = QHBoxLayout()
        f_row.setContentsMargins(4, 0, 4, 0)
        
        hint = QLabel("↑↓ Navigate   •   ↵ Open   •   Esc Close")
        hint.setFont(QFont("Inter", 10))
        hint.setStyleSheet("color: #64748B;")

        thaid_tag = QLabel("⚡ Theonix Omni-Search")
        thaid_tag.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        thaid_tag.setStyleSheet("color: #00FFAA;")

        f_row.addWidget(hint)
        f_row.addStretch()
        f_row.addWidget(thaid_tag)
        c_layout.addLayout(f_row)

        layout.addWidget(self.container)

    def _on_text_changed(self, text: str):
        self._load_results(text)

    def _load_results(self, text: str):
        self.results_list.clear()
        results = self.engine.search(text)

        for res in results:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, res)

            # Custom Item Widget
            w = QWidget()
            w_lay = QHBoxLayout(w)
            w_lay.setContentsMargins(6, 4, 6, 4)
            w_lay.setSpacing(12)

            t_lay = QVBoxLayout()
            t_lay.setSpacing(2)
            
            title = QLabel(res["title"])
            title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
            title.setStyleSheet("color: #F4F7FB;")
            
            sub = QLabel(res["subtitle"])
            sub.setFont(QFont("Inter", 10))
            sub.setStyleSheet("color: #94A3B8;")

            t_lay.addWidget(title)
            t_lay.addWidget(sub)
            w_lay.addLayout(t_lay)
            w_lay.addStretch()

            # Category Pill Badge
            badge = QLabel(res.get("category", "General"))
            b_color = res.get("badge_color", "#00FFAA")
            badge.setStyleSheet(f"""
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {b_color};
                border-radius: 6px;
                padding: 2px 8px;
                color: {b_color};
                font-size: 10px;
                font-weight: bold;
            """)
            w_lay.addWidget(badge)

            item.setSizeHint(w.sizeHint())
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, w)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_item_activated(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and "exec" in data:
            cmd = data["exec"]
            self.hide()
            try:
                subprocess.Popen(cmd, shell=True)
            except Exception as e:
                print(f"[SearchService] Execution failed: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            curr = self.results_list.currentItem()
            if curr:
                self._on_item_activated(curr)
        elif event.key() == Qt.Key.Key_Down:
            curr_row = self.results_list.currentRow()
            if curr_row < self.results_list.count() - 1:
                self.results_list.setCurrentRow(curr_row + 1)
        elif event.key() == Qt.Key.Key_Up:
            curr_row = self.results_list.currentRow()
            if curr_row > 0:
                self.results_list.setCurrentRow(curr_row - 1)
        else:
            super().keyPressEvent(event)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.input_field.clear()
            self.engine.reindex()
            self._load_results("")
            self.show()
            self.raise_()
            self.activateWindow()
            self.input_field.setFocus()


# =============================================================================
# D-BUS SERVICE DAEMON
# =============================================================================

class SearchService(QObject):
    toggled = pyqtSignal(bool)

    def __init__(self, overlay: GlassSpotlightOverlay, engine: SearchEngine):
        super().__init__()
        self.overlay = overlay
        self.engine = engine

    @pyqtSlot(result=bool)
    def Toggle(self) -> bool:
        self.overlay.toggle()
        self.toggled.emit(self.overlay.isVisible())
        return self.overlay.isVisible()

    @pyqtSlot(str, int, result=str)
    def Query(self, query_text: str, limit: int = 8) -> str:
        results = self.engine.search(query_text, limit=limit)
        return json.dumps(results)

    @pyqtSlot(result=bool)
    def Reindex(self) -> bool:
        self.engine.reindex()
        return True


def main():
    app = QApplication(sys.argv)
    bus = QDBusConnection.sessionBus()

    engine = SearchEngine()
    overlay = GlassSpotlightOverlay(engine)
    service = SearchService(overlay, engine)

    if not bus.registerService("org.theonix.Search"):
        # Service already running, toggle it
        from PyQt6.QtDBus import QDBusMessage
        msg = QDBusMessage.createMethodCall("org.theonix.Search", "/org/theonix/Search", "", "Toggle")
        bus.call(msg)
        sys.exit(0)

    if not bus.registerObject("/org/theonix/Search", service, QDBusConnection.RegisterOption.ExportAllSlots | QDBusConnection.RegisterOption.ExportAllSignals):
        print("[SearchService] Failed to register object at /org/theonix/Search")
        sys.exit(1)

    if "--daemon" not in sys.argv:
        overlay.toggle()

    print("[SearchService] Theonix Global Omni-Search active on org.theonix.Search")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
