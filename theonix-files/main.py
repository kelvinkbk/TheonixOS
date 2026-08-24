#!/usr/bin/env python3
"""
Theonix Files — Ultra-Dark Glassmorphic File Manager for Theonix OS
Features breadcrumb path navigation, live file search, dotfiles toggle, and automatic UACL compatibility.
"""

import os
import shutil
import subprocess
import sys
import time
from PyQt6.QtCore import Qt, QDir, QModelIndex, QSortFilterProxyModel
from PyQt6.QtGui import QFont, QFileSystemModel, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QLabel, QSplitter, QHeaderView,
    QMenu, QMessageBox, QInputDialog, QFrame, QButtonGroup
)

THEME_QSS = """
QMainWindow {
    background-color: #07090E;
}

QWidget#CentralWidget {
    background-color: #07090E;
    color: #F8FAFC;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Places Sidebar Container */
QWidget#SidebarContainer {
    background-color: #0B0E17;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Places Buttons */
QPushButton.NavBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    margin: 2px 10px;
}

QPushButton.NavBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #FFFFFF;
}

QPushButton.NavBtn:checked {
    background-color: rgba(108, 99, 255, 0.2);
    border-left: 3px solid #00FFAA;
    color: #FFFFFF;
    font-weight: 700;
}

/* Top Toolbar */
QFrame#TopBar {
    background-color: #0E121C;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px 14px;
}

QLineEdit#PathBar, QLineEdit#SearchBox {
    background-color: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 7px 14px;
    color: #FFFFFF;
    font-size: 13px;
}

QLineEdit#PathBar:focus, QLineEdit#SearchBox:focus {
    border: 1px solid #00FFAA;
}

QPushButton.TopNavBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 7px;
    font-size: 13px;
    padding: 6px 12px;
}

QPushButton.TopNavBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #00FFAA;
}

/* File Tree/List View */
QTreeView#FileView {
    background-color: #07090E;
    border: none;
    color: #F8FAFC;
    font-size: 13px;
    outline: none;
}

QTreeView#FileView::item {
    height: 38px;
    padding: 2px 10px;
}

QTreeView#FileView::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
}

QTreeView#FileView::item:selected {
    background-color: rgba(108, 99, 255, 0.25);
    border: 1px solid rgba(0, 255, 170, 0.3);
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0E121C;
    color: #94A3B8;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px 12px;
    font-weight: bold;
    font-size: 12px;
}

/* Inspector Drawer */
QFrame#Inspector {
    background-color: #0B0E17;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
    padding: 16px;
}
"""


class TheonixFilesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Files")
        self.setMinimumSize(980, 640)
        self.resize(1120, 740)
        self.history = []
        self.history_idx = -1
        self.show_hidden = False

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        t_layout = QHBoxLayout(top_bar)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(8)

        self.back_btn = QPushButton("◀")
        self.back_btn.setProperty("class", "TopNavBtn")
        self.back_btn.clicked.connect(self._nav_back)
        t_layout.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "TopNavBtn")
        self.fwd_btn.clicked.connect(self._nav_forward)
        t_layout.addWidget(self.fwd_btn)

        self.up_btn = QPushButton("⬆")
        self.up_btn.setProperty("class", "TopNavBtn")
        self.up_btn.clicked.connect(self._nav_up)
        t_layout.addWidget(self.up_btn)

        self.path_bar = QLineEdit()
        self.path_bar.setObjectName("PathBar")
        self.path_bar.returnPressed.connect(self._on_path_entered)
        t_layout.addWidget(self.path_bar, 1)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Filter files (Ctrl+F)...")
        self.search_box.setFixedWidth(160)
        self.search_box.textChanged.connect(self._on_filter_text_changed)
        t_layout.addWidget(self.search_box)

        self.hidden_btn = QPushButton("👁️ Dotfiles")
        self.hidden_btn.setProperty("class", "TopNavBtn")
        self.hidden_btn.clicked.connect(self._toggle_hidden)
        t_layout.addWidget(self.hidden_btn)

        term_btn = QPushButton("Terminal")
        term_btn.setProperty("class", "TopNavBtn")
        term_btn.clicked.connect(self._open_terminal)
        t_layout.addWidget(term_btn)

        main_layout.addWidget(top_bar)

        # Splitter: Sidebar + File List + Inspector
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Places sidebar container
        sidebar_box = QWidget()
        sidebar_box.setObjectName("SidebarContainer")
        sidebar_box.setFixedWidth(230)
        sb_layout = QVBoxLayout(sidebar_box)
        sb_layout.setContentsMargins(0, 18, 0, 18)
        sb_layout.setSpacing(4)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(20, 0, 20, 14)
        brand_icon = QLabel("📁")
        brand_icon.setStyleSheet("font-size: 18px;")
        brand_title = QLabel("THEONIX")
        brand_title.setStyleSheet("font-size: 14px; font-weight: 900; letter-spacing: 1px; color: #FFFFFF;")
        brand_tag = QLabel("FILES")
        brand_tag.setStyleSheet("font-size: 10.5px; font-weight: bold; background: rgba(0,212,255,0.15); color: #00D4FF; padding: 2px 6px; border-radius: 4px;")
        
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
            btn = QPushButton(label)
            btn.setProperty("class", "NavBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.inspector.setObjectName("Inspector")
        self.inspector.setFixedWidth(240)
        ins_layout = QVBoxLayout(self.inspector)
        ins_layout.setContentsMargins(14, 16, 14, 16)
        ins_layout.setSpacing(12)

        ins_hdr = QLabel("ℹ️ File Properties")
        ins_hdr.setStyleSheet("font-size: 14px; font-weight: bold; color: #00FFAA;")
        ins_layout.addWidget(ins_hdr)

        self.ins_icon = QLabel("📁")
        self.ins_icon.setStyleSheet("font-size: 38px; text-align: center;")
        self.ins_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ins_layout.addWidget(self.ins_icon)

        self.ins_name = QLabel("Select a file or directory")
        self.ins_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
        self.ins_name.setWordWrap(True)
        ins_layout.addWidget(self.ins_name)

        self.ins_detail = QLabel("No item selected.")
        self.ins_detail.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.ins_detail.setWordWrap(True)
        ins_layout.addWidget(self.ins_detail)

        self.ins_uacl_btn = QPushButton("🚀 Run with UACL")
        self.ins_uacl_btn.setProperty("class", "TopNavBtn")
        self.ins_uacl_btn.setVisible(False)
        ins_layout.addWidget(self.ins_uacl_btn)

        ins_layout.addStretch()
        self.splitter.addWidget(self.inspector)

        self.splitter.setSizes([230, 680, 210])
        main_layout.addWidget(self.splitter, 1)

        self.btn_group.idClicked.connect(self._on_place_selected)
        first_btn = self.btn_group.button(0)
        if first_btn:
            first_btn.setChecked(True)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Ctrl+H"), self, self._toggle_hidden)
        QShortcut(QKeySequence("F4"), self, self._open_terminal)

        self._navigate_to(user_home)

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
        self.proxy_model.setFilterFixedString(text)

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
            if lower.endswith((".exe", ".msi", ".deb", ".appimage")):
                self.ins_icon.setText("⚙️")
                self.ins_uacl_btn.setVisible(True)
                self.ins_uacl_btn.clicked.disconnect() if self.ins_uacl_btn.receivers(self.ins_uacl_btn.clicked) > 0 else None
                self.ins_uacl_btn.clicked.connect(lambda: subprocess.Popen(["theonix-uacl", "launch", "--path", path]))
            else:
                self.ins_icon.setText("📄")
                self.ins_uacl_btn.setVisible(False)

            try:
                sz = os.path.getsize(path)
                sz_str = f"{sz / 1024:.1f} KB" if sz < 1024**2 else f"{sz / 1024**2:.1f} MB"
                mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(path)))
                self.ins_detail.setText(f"File Size: {sz_str}\nModified: {mtime}\nPath: {path}")
            except Exception:
                self.ins_detail.setText(f"Path: {path}")

    def _on_item_double_clicked(self, index: QModelIndex):
        src_idx = self.proxy_model.mapToSource(index)
        path = self.base_model.filePath(src_idx)
        if os.path.isdir(path):
            self._navigate_to(path)
        else:
            lower = path.lower()
            if lower.endswith((".exe", ".msi", ".deb", ".appimage")):
                subprocess.Popen(["theonix-uacl", "launch", "--path", path])
            else:
                subprocess.Popen(["xdg-open", path])

    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self)

        if index.isValid():
            src_idx = self.proxy_model.mapToSource(index)
            path = self.base_model.filePath(src_idx)
            open_act = menu.addAction("Open")
            open_act.triggered.connect(lambda: self._on_item_double_clicked(index))

            if path.lower().endswith((".exe", ".deb", ".appimage")):
                uacl_act = menu.addAction("🚀 Launch with Theonix UACL")
                uacl_act.triggered.connect(lambda: subprocess.Popen(["theonix-uacl", "launch", "--path", path]))

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
    app.setStyle("Fusion")
    app.setStyleSheet(THEME_QSS)
    win = TheonixFilesWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
