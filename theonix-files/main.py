#!/usr/bin/env python3
"""
Theonix Files — Ultra-Dark Glassmorphic File Manager for Theonix OS.
Powered by theonix_core platform services with Spacebar Quick Look, THAID AI File Intelligence, and advanced query filters.
"""

import os
import shutil
import subprocess
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")))

from PyQt6.QtCore import Qt, QDir, QModelIndex, QSortFilterProxyModel, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QFileSystemModel, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QLabel, QSplitter, QHeaderView,
    QMenu, QMessageBox, QInputDialog, QFrame, QButtonGroup, QTextEdit
)

from theonix_core import (
    THEONIX_THEME_QSS, GlassCard, NavButton, Badge,
    SearchBar, QuickLookDialog, apply_theonix_style,
    SearchService, UACLService, AIService
)


class AIFileWorker(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, prompt: str, file_path: str = ""):
        super().__init__()
        self.prompt = prompt
        self.file_path = file_path

    def run(self):
        file_content = ""
        if self.file_path and os.path.isfile(self.file_path):
            try:
                # Read up to 8k chars of text
                with open(self.file_path, "r", errors="ignore") as f:
                    file_content = f.read(8000)
            except Exception:
                pass

        system_msg = (
            "You are THAID, the native AI assistant in Theonix Files.\n"
            "You analyze files, summarize documentation, explain source code, and help organize the filesystem."
        )

        user_content = self.prompt
        if file_content:
            user_content = f"File Target: {self.file_path}\n```\n{file_content}\n```\n\nTask: {self.prompt}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content}
        ]

        try:
            for token in AIService.stream_chat(messages, model_id="1.5b"):
                self.chunk_received.emit(token)
        except Exception as e:
            self.chunk_received.emit(f"\n[THAID Connection Error: {e}]\n")
        self.finished.emit()


class TheonixFilesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Files")
        self.setMinimumSize(1020, 680)
        self.resize(1180, 760)
        self.history = []
        self.history_idx = -1
        self.show_hidden = False
        self.ai_worker = None

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #0E121C; border-bottom: 1px solid rgba(255,255,255,0.08); padding: 8px 14px;")
        t_layout = QHBoxLayout(top_bar)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(8)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "ActionBtn")
        self.back_btn.clicked.connect(self._nav_back)
        t_layout.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "ActionBtn")
        self.fwd_btn.clicked.connect(self._nav_forward)
        t_layout.addWidget(self.fwd_btn)

        self.up_btn = QPushButton("⬆")
        self.up_btn.setProperty("class", "ActionBtn")
        self.up_btn.clicked.connect(self._nav_up)
        t_layout.addWidget(self.up_btn)

        self.path_bar = QLineEdit()
        self.path_bar.setPlaceholderText("Enter path...")
        self.path_bar.returnPressed.connect(self._on_path_entered)
        t_layout.addWidget(self.path_bar, 1)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search or filter (e.g. ext:png)...")
        self.search_box.setFixedWidth(210)
        self.search_box.textChanged.connect(self._on_filter_text_changed)
        t_layout.addWidget(self.search_box)

        self.hidden_btn = QPushButton("👁️ Dotfiles")
        self.hidden_btn.setProperty("class", "ActionBtn")
        self.hidden_btn.clicked.connect(self._toggle_hidden)
        t_layout.addWidget(self.hidden_btn)

        term_btn = QPushButton("Terminal")
        term_btn.setProperty("class", "ActionBtn")
        term_btn.clicked.connect(self._open_terminal)
        t_layout.addWidget(term_btn)

        self.ai_btn = QPushButton("✨ Ask THAID")
        self.ai_btn.setProperty("class", "PrimaryBtn")
        self.ai_btn.clicked.connect(self._toggle_ai_drawer)
        t_layout.addWidget(self.ai_btn)

        main_layout.addWidget(top_bar)

        # Splitter: Sidebar + File List + Inspector + AI Drawer
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Places sidebar container
        sidebar_box = QWidget()
        sidebar_box.setObjectName("SidebarContainer")
        sidebar_box.setFixedWidth(220)
        sb_layout = QVBoxLayout(sidebar_box)
        sb_layout.setContentsMargins(0, 18, 0, 18)
        sb_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(20, 0, 20, 14)
        brand_icon = QLabel("📁")
        brand_icon.setStyleSheet("font-size: 18px;")
        brand_title = QLabel("THEONIX")
        brand_title.setStyleSheet("font-size: 14px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;")
        brand_tag = Badge("FILES", "blue")
        
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title)
        brand_row.addWidget(brand_tag)
        brand_row.addStretch()
        sb_layout.addLayout(brand_row)

        user_home = os.path.expanduser("~")
        self.places_items = [
            ("🏠  Home", user_home),
            ("🖥️  Desktop", os.path.join(user_home, "Desktop")),
            ("📥  Downloads", os.path.join(user_home, "Downloads")),
            ("📄  Documents", os.path.join(user_home, "Documents")),
            ("🖼️  Pictures", os.path.join(user_home, "Pictures")),
            ("🎵  Music", os.path.join(user_home, "Music")),
            ("🎬  Videos", os.path.join(user_home, "Videos")),
            ("💽  Root FileSystem (/)", "/"),
        ]

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for idx, (label, pth) in enumerate(self.places_items):
            btn = NavButton(label)
            self.btn_group.addButton(btn, idx)
            sb_layout.addWidget(btn)

        sb_layout.addStretch()
        self.splitter.addWidget(sidebar_box)

        # File Tree Model with Proxy Filter
        self.base_model = QFileSystemModel()
        self.base_model.setRootPath("")
        self._update_filter_flags()

        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.base_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.tree = QTreeView()
        self.tree.setObjectName("FileView")
        self.tree.setModel(self.proxy_model)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setSortingEnabled(True)
        self.tree.doubleClicked.connect(self._on_item_double_clicked)
        self.tree.clicked.connect(self._on_item_selected)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.splitter.addWidget(self.tree)

        # Inspector Panel
        self.inspector = QFrame()
        self.inspector.setStyleSheet("background-color: #0B0E17; border-left: 1px solid rgba(255,255,255,0.08); padding: 14px;")
        self.inspector.setFixedWidth(230)
        ins_layout = QVBoxLayout(self.inspector)
        ins_layout.setContentsMargins(12, 14, 12, 14)
        ins_layout.setSpacing(10)

        ins_hdr = QLabel("ℹ️ File Properties")
        ins_hdr.setStyleSheet("font-size: 13.5px; font-weight: bold; color: #00FFAA;")
        ins_layout.addWidget(ins_hdr)

        self.ins_icon = QLabel("📁")
        self.ins_icon.setStyleSheet("font-size: 36px; text-align: center;")
        self.ins_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ins_layout.addWidget(self.ins_icon)

        self.ins_name = QLabel("Select an item")
        self.ins_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
        self.ins_name.setWordWrap(True)
        ins_layout.addWidget(self.ins_name)

        self.ins_detail = QLabel("Press Space for Quick Look preview.")
        self.ins_detail.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.ins_detail.setWordWrap(True)
        ins_layout.addWidget(self.ins_detail)

        self.ins_quick_look_btn = QPushButton("👁️ Quick Look (Space)")
        self.ins_quick_look_btn.setProperty("class", "ActionBtn")
        self.ins_quick_look_btn.clicked.connect(self._open_quick_look)
        ins_layout.addWidget(self.ins_quick_look_btn)

        self.ins_ai_btn = QPushButton("✨ Summarize with AI")
        self.ins_ai_btn.setProperty("class", "PrimaryBtn")
        self.ins_ai_btn.clicked.connect(self._summarize_selected_file)
        ins_layout.addWidget(self.ins_ai_btn)

        self.ins_uacl_btn = QPushButton("🚀 Run with UACL")
        self.ins_uacl_btn.setProperty("class", "PrimaryBtn")
        self.ins_uacl_btn.setVisible(False)
        ins_layout.addWidget(self.ins_uacl_btn)

        ins_layout.addStretch()
        self.splitter.addWidget(self.inspector)

        # AI Assistant Sidebar
        self.ai_sidebar = QFrame()
        self.ai_sidebar.setStyleSheet("background-color: #080A10; border-left: 1px solid rgba(255,255,255,0.08); padding: 14px;")
        self.ai_sidebar.setFixedWidth(280)
        ai_layout = QVBoxLayout(self.ai_sidebar)
        ai_layout.setContentsMargins(12, 14, 12, 14)
        ai_layout.setSpacing(10)

        ai_hdr = QHBoxLayout()
        ai_title = QLabel("🤖 THAID Files")
        ai_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00FFAA;")
        ai_hdr.addWidget(ai_title)
        ai_hdr.addStretch()
        ai_hdr.addWidget(Badge("AI ACTIVE", "cyan"))
        ai_layout.addLayout(ai_hdr)

        self.ai_log = QTextEdit()
        self.ai_log.setReadOnly(True)
        self.ai_log.setStyleSheet(
            "background-color: rgba(14, 18, 28, 0.9); border: 1px solid rgba(255,255,255,0.08); "
            "border-radius: 8px; color: #F8FAFC; padding: 8px; font-size: 12px; line-height: 1.4;"
        )
        self.ai_log.setPlaceholderText("Select a file to summarize, analyze code, or ask questions...")
        ai_layout.addWidget(self.ai_log)

        ai_input_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask THAID about files...")
        self.ai_input.returnPressed.connect(self._send_ai_file_query)
        ai_send = QPushButton("Ask")
        ai_send.setProperty("class", "PrimaryBtn")
        ai_send.clicked.connect(self._send_ai_file_query)
        ai_input_row.addWidget(self.ai_input)
        ai_input_row.addWidget(ai_send)
        ai_layout.addLayout(ai_input_row)

        self.splitter.addWidget(self.ai_sidebar)
        self.ai_sidebar.setVisible(False)

        self.splitter.setSizes([220, 580, 220, 280])
        main_layout.addWidget(self.splitter, 1)

        self.btn_group.idClicked.connect(self._on_place_selected)
        first_btn = self.btn_group.button(0)
        if first_btn:
            first_btn.setChecked(True)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Ctrl+H"), self, self._toggle_hidden)
        QShortcut(QKeySequence("F4"), self, self._open_terminal)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self.tree, self._open_quick_look)

        self.current_selected_path = user_home
        self._navigate_to(user_home)

    def _toggle_ai_drawer(self):
        self.ai_sidebar.setVisible(not self.ai_sidebar.isVisible())

    def _update_filter_flags(self):
        filters = QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot
        if self.show_hidden:
            filters |= QDir.Filter.Hidden
        self.base_model.setFilter(filters)

    def _toggle_hidden(self):
        self.show_hidden = not self.show_hidden
        self._update_filter_flags()
        self.hidden_btn.setStyleSheet("color: #00FFAA;" if self.show_hidden else "color: #94A3B8;")

    def _on_filter_text_changed(self, text):
        query_data = SearchService.parse_file_query(text)
        filter_str = query_data["text"] or (f".{query_data['ext']}" if query_data["ext"] else text)
        self.proxy_model.setFilterFixedString(filter_str)

    def _navigate_to(self, path: str, record_history: bool = True):
        if not os.path.exists(path):
            return
        src_index = self.base_model.index(path)
        proxy_index = self.proxy_model.mapFromSource(src_index)
        self.tree.setRootIndex(proxy_index)
        self.path_bar.setText(path)

        if record_history:
            self.history = self.history[:self.history_idx + 1]
            self.history.append(path)
            self.history_idx += 1

    def _on_place_selected(self, idx):
        if 0 <= idx < len(self.places_items):
            path = self.places_items[idx][1]
            self._navigate_to(path)

    def _on_path_entered(self):
        pth = self.path_bar.text().strip()
        if os.path.exists(pth):
            self._navigate_to(pth)

    def _nav_back(self):
        if self.history_idx > 0:
            self.history_idx -= 1
            self._navigate_to(self.history[self.history_idx], record_history=False)

    def _nav_forward(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self._navigate_to(self.history[self.history_idx], record_history=False)

    def _nav_up(self):
        cur = self.path_bar.text()
        parent = os.path.dirname(cur)
        if os.path.exists(parent):
            self._navigate_to(parent)

    def _open_terminal(self):
        cur = self.path_bar.text()
        subprocess.Popen(["konsole", "--workdir", cur])

    def _on_item_selected(self, index: QModelIndex):
        src_idx = self.proxy_model.mapToSource(index)
        path = self.base_model.filePath(src_idx)
        self.current_selected_path = path
        name = os.path.basename(path) or "/"
        self.ins_name.setText(name)

        if os.path.isdir(path):
            self.ins_icon.setText("📁")
            try:
                count = len(os.listdir(path))
                self.ins_detail.setText(f"Folder\nItems: {count}\nPath: {path}")
            except Exception:
                self.ins_detail.setText(f"Folder\nPath: {path}")
            self.ins_uacl_btn.setVisible(False)
        else:
            lower = name.lower()
            if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".svg")):
                self.ins_icon.setText("🖼️")
            elif lower.endswith((".py", ".rs", ".js", ".html", ".cpp", ".c", ".sh")):
                self.ins_icon.setText("💻")
            elif lower.endswith((".mp3", ".flac", ".wav", ".ogg")):
                self.ins_icon.setText("🎵")
            elif lower.endswith((".mp4", ".mkv", ".webm")):
                self.ins_icon.setText("🎬")
            elif lower.endswith((".zip", ".tar.gz", ".zst", ".7z")):
                self.ins_icon.setText("📦")
            elif lower.endswith((".exe", ".msi")):
                self.ins_icon.setText("🪟")
            else:
                self.ins_icon.setText("📄")

            try:
                size_b = os.path.getsize(path)
                size_str = f"{size_b / (1024*1024):.2f} MB" if size_b > 1024*1024 else f"{size_b / 1024:.1f} KB"
                self.ins_detail.setText(f"File\nSize: {size_str}\nPath: {path}")
            except Exception:
                self.ins_detail.setText(f"Path: {path}")

            if lower.endswith((".exe", ".deb", ".appimage")):
                self.ins_uacl_btn.setVisible(True)
                self.ins_uacl_btn.clicked.disconnect()
                self.ins_uacl_btn.clicked.connect(lambda: UACLService.launch(path))
            else:
                self.ins_uacl_btn.setVisible(False)

    def _on_item_double_clicked(self, index: QModelIndex):
        src_idx = self.proxy_model.mapToSource(index)
        path = self.base_model.filePath(src_idx)
        if os.path.isdir(path):
            self._navigate_to(path)
        else:
            if path.lower().endswith((".exe", ".deb", ".appimage")):
                UACLService.launch(path)
            else:
                subprocess.Popen(["xdg-open", path], stderr=subprocess.DEVNULL)

    def _open_quick_look(self):
        if self.current_selected_path and os.path.exists(self.current_selected_path):
            dlg = QuickLookDialog(self.current_selected_path, self)
            dlg.exec()

    def _summarize_selected_file(self):
        if not self.current_selected_path or not os.path.isfile(self.current_selected_path):
            QMessageBox.information(self, "THAID Files", "Please select a document or code file to summarize.")
            return

        self.ai_sidebar.setVisible(True)
        fname = os.path.basename(self.current_selected_path)
        self.ai_log.append(f"<b>You:</b> Summarize <code>{fname}</code>\n")
        self.ai_log.append("<b>THAID:</b> <i>Reading file & summarizing...</i>\n")

        self.ai_worker = AIFileWorker(
            prompt="Please provide a concise summary and breakdown of the contents of this file.",
            file_path=self.current_selected_path
        )
        self.ai_worker.chunk_received.connect(lambda c: self.ai_log.append(c))
        self.ai_worker.start()

    def _send_ai_file_query(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_input.clear()
        self.ai_sidebar.setVisible(True)
        self.ai_log.append(f"<b>You:</b> {text}\n")
        self.ai_log.append("<b>THAID:</b> <i>Thinking...</i>\n")

        self.ai_worker = AIFileWorker(prompt=text, file_path=self.current_selected_path)
        self.ai_worker.chunk_received.connect(lambda c: self.ai_log.append(c))
        self.ai_worker.start()

    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #121826; border: 1px solid #1E2638; border-radius: 8px; padding: 6px; }
            QMenu::item { padding: 6px 20px; color: #F8FAFC; border-radius: 4px; }
            QMenu::item:selected { background-color: rgba(0, 255, 170, 0.15); color: #00FFAA; }
        """)

        if index.isValid():
            src_idx = self.proxy_model.mapToSource(index)
            path = self.base_model.filePath(src_idx)
            
            ql_act = menu.addAction("👁️ Quick Look (Space)")
            ql_act.triggered.connect(self._open_quick_look)

            open_act = menu.addAction("Open")
            open_act.triggered.connect(lambda: self._on_item_double_clicked(index))

            if os.path.isfile(path):
                ai_sum_act = menu.addAction("✨ Summarize with THAID")
                ai_sum_act.triggered.connect(self._summarize_selected_file)

            if path.lower().endswith((".exe", ".deb", ".appimage")):
                uacl_act = menu.addAction("🚀 Launch with Theonix UACL")
                uacl_act.triggered.connect(lambda: UACLService.launch(path))

            menu.addSeparator()
            del_act = menu.addAction("Delete")
            del_act.triggered.connect(lambda: self._delete_item(path))
        else:
            new_folder_act = menu.addAction("New Folder")
            new_folder_act.triggered.connect(self._create_folder)

        term_act = menu.addAction("Open in Terminal")
        term_act.triggered.connect(self._open_terminal)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _create_folder(self):
        cur = self.path_bar.text()
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            os.makedirs(os.path.join(cur, name), exist_ok=True)

    def _delete_item(self, path):
        reply = QMessageBox.question(self, "Delete", f"Delete '{os.path.basename(path)}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")


def main():
    app = QApplication(sys.argv)
    apply_theonix_style(app)
    win = TheonixFilesWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
