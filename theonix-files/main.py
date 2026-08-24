#!/usr/bin/env python3
"""
Theonix Files — High-Performance, Modern File Manager for Theonix OS
Features breadcrumb navigation, quick places, and automatic UACL compatibility.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from PyQt6.QtCore import Qt, QDir, QSize, QModelIndex
from PyQt6.QtGui import QFont, QIcon, QAction, QKeySequence, QFileSystemModel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QListView, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QHeaderView, QMenu, QMessageBox, QInputDialog,
    QFileDialog, QFrame
)

THEME_QSS = """
QMainWindow {
    background-color: #0B0E14;
}

QWidget#CentralWidget {
    background-color: #0B0E14;
    color: #F0F4F8;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Places Sidebar */
QListWidget#PlacesSidebar {
    background-color: #121620;
    border: none;
    border-right: 1px solid #1E2638;
    outline: none;
    padding-top: 10px;
}

QListWidget#PlacesSidebar::item {
    color: #94A3B8;
    height: 42px;
    padding-left: 14px;
    margin: 2px 6px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}

QListWidget#PlacesSidebar::item:hover {
    background-color: rgba(108, 99, 255, 0.12);
    color: #FFFFFF;
}

QListWidget#PlacesSidebar::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    font-weight: bold;
}

/* Top Toolbar */
QFrame#TopBar {
    background-color: #121620;
    border-bottom: 1px solid #1E2638;
    padding: 8px 12px;
}

QLineEdit#PathBar {
    background-color: #161D2B;
    border: 1px solid #28354D;
    border-radius: 8px;
    padding: 6px 14px;
    color: #FFFFFF;
    font-size: 13px;
}

QLineEdit#PathBar:focus {
    border: 1px solid #00FFAA;
}

QPushButton.NavBtn {
    background-color: #1A2232;
    color: #F0F4F8;
    border: 1px solid #28354D;
    border-radius: 6px;
    font-size: 14px;
    padding: 6px 10px;
}

QPushButton.NavBtn:hover {
    background-color: #26334D;
    color: #00FFAA;
}

/* File Tree/List View */
QTreeView#FileView {
    background-color: #0F131C;
    border: none;
    color: #F0F4F8;
    font-size: 13px;
    outline: none;
}

QTreeView#FileView::item {
    height: 36px;
    padding: 2px 8px;
}

QTreeView#FileView::item:hover {
    background-color: #161D2B;
}

QTreeView#FileView::item:selected {
    background-color: #232E42;
    color: #00FFAA;
}

QHeaderView::section {
    background-color: #121620;
    color: #94A3B8;
    border: none;
    border-bottom: 1px solid #1E2638;
    padding: 6px 10px;
    font-weight: bold;
    font-size: 12px;
}
"""


class TheonixFilesWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theonix Files")
        self.setMinimumSize(980, 640)
        self.resize(1100, 720)
        self.history = []
        self.history_idx = -1

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
        self.back_btn.setProperty("class", "NavBtn")
        self.back_btn.clicked.connect(self._nav_back)
        t_layout.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("▶")
        self.fwd_btn.setProperty("class", "NavBtn")
        self.fwd_btn.clicked.connect(self._nav_forward)
        t_layout.addWidget(self.fwd_btn)

        self.up_btn = QPushButton("⬆")
        self.up_btn.setProperty("class", "NavBtn")
        self.up_btn.clicked.connect(self._nav_up)
        t_layout.addWidget(self.up_btn)

        self.path_bar = QLineEdit()
        self.path_bar.setObjectName("PathBar")
        self.path_bar.returnPressed.connect(self._on_path_entered)
        t_layout.addWidget(self.path_bar, 1)

        term_btn = QPushButton("Terminal")
        term_btn.setProperty("class", "NavBtn")
        term_btn.clicked.connect(self._open_terminal)
        t_layout.addWidget(term_btn)

        main_layout.addWidget(top_bar)

        # Splitter: Sidebar + File List
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Places sidebar
        self.places = QListWidget()
        self.places.setObjectName("PlacesSidebar")
        self.places.setFixedWidth(200)

        user_home = os.path.expanduser("~")
        places_items = [
            ("🏠  Home", user_home),
            ("🖥️  Desktop", os.path.join(user_home, "Desktop")),
            ("📥  Downloads", os.path.join(user_home, "Downloads")),
            ("📄  Documents", os.path.join(user_home, "Documents")),
            ("🖼️  Pictures", os.path.join(user_home, "Pictures")),
            ("🎵  Music", os.path.join(user_home, "Music")),
            ("🎬  Videos", os.path.join(user_home, "Videos")),
            ("💽  Root (/)", "/"),
        ]

        for label, pth in places_items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, pth)
            self.places.addItem(item)

        self.places.currentRowChanged.connect(self._on_place_selected)
        splitter.addWidget(self.places)

        # File Tree Model
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView()
        self.tree.setObjectName("FileView")
        self.tree.setModel(self.model)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setSortingEnabled(True)
        self.tree.doubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        # Adjust header columns
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        splitter.addWidget(self.tree)
        splitter.setSizes([200, 800])
        main_layout.addWidget(splitter, 1)

        self._navigate_to(user_home)

    def _navigate_to(self, path: str, record_history: bool = True):
        if not os.path.exists(path):
            return
        index = self.model.index(path)
        self.tree.setRootIndex(index)
        self.path_bar.setText(path)

        if record_history:
            self.history = self.history[:self.history_idx + 1]
            self.history.append(path)
            self.history_idx += 1

    def _on_place_selected(self, idx):
        item = self.places.item(idx)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
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

    def _on_item_double_clicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self._navigate_to(path)
        else:
            # Check for Windows / UACL executables
            lower = path.lower()
            if lower.endswith((".exe", ".msi", ".deb", ".appimage")):
                subprocess.Popen(["theonix-uacl", "launch", "--path", path])
            else:
                subprocess.Popen(["xdg-open", path])

    def _show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self)

        if index.isValid():
            path = self.model.filePath(index)
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
    app.setStyleSheet(THEME_QSS)
    win = TheonixFilesWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
