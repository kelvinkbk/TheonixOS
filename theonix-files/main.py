#!/usr/bin/env python3
"""
Theonix Files — Ultra-Dark Glassmorphic File Manager for Theonix OS
Features breadcrumb navigation, quick places, and automatic UACL compatibility.
"""

import os
import shutil
import subprocess
import sys
from PyQt6.QtCore import Qt, QDir, QModelIndex
from PyQt6.QtGui import QFont, QFileSystemModel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QListWidget, QListWidgetItem,
    QLabel, QSplitter, QHeaderView, QMenu, QMessageBox, QInputDialog,
    QFrame
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

/* Places Sidebar */
QListWidget#PlacesSidebar {
    background-color: #0E121C;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    outline: none;
    padding-top: 14px;
}

QListWidget#PlacesSidebar::item {
    color: #94A3B8;
    height: 44px;
    padding-left: 16px;
    margin: 2px 8px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
}

QListWidget#PlacesSidebar::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
}

QListWidget#PlacesSidebar::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(108, 99, 255, 0.35), stop:1 rgba(0, 255, 170, 0.25));
    border: 1px solid rgba(0, 255, 170, 0.4);
    color: #FFFFFF;
    font-weight: 600;
}

/* Top Toolbar */
QFrame#TopBar {
    background-color: #0E121C;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px 14px;
}

QLineEdit#PathBar {
    background-color: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 7px 16px;
    color: #FFFFFF;
    font-size: 13px;
}

QLineEdit#PathBar:focus {
    border: 1px solid #00FFAA;
}

QPushButton.NavBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 7px;
    font-size: 13px;
    padding: 6px 12px;
}

QPushButton.NavBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    color: #00FFAA;
}

/* File Tree/List View */
QTreeView#FileView {
    background-color: #0B0E14;
    border: none;
    color: #F8FAFC;
    font-size: 13px;
    outline: none;
}

QTreeView#FileView::item {
    height: 38px;
    padding: 2px 10px;
    border-radius: 4px;
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
        self.places.setFixedWidth(210)

        user_home = os.path.expanduser("~")
        places_items = [
            ("🏠  Home", user_home),
            ("🖥️  Desktop", os.path.join(user_home, "Desktop")),
            ("📥  Downloads", os.path.join(user_home, "Downloads")),
            ("📄  Documents", os.path.join(user_home, "Documents")),
            ("🖼️  Pictures", os.path.join(user_home, "Pictures")),
            ("🎵  Music", os.path.join(user_home, "Music")),
            ("🎬  Videos", os.path.join(user_home, "Videos")),
            ("💽  Root FileSystem (/)", "/"),
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

        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        splitter.addWidget(self.tree)
        splitter.setSizes([210, 850])
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
