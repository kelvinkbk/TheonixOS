"""
Theonix Core UI — Unified Glassmorphic Design System & Common Widgets.
"""

import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QImageReader
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QLabel,
    QLineEdit, QProgressBar, QVBoxLayout, QHBoxLayout,
    QDialog, QTextEdit, QScrollArea
)

THEONIX_THEME_QSS = """
QMainWindow {
    background-color: #07090E;
}

QWidget#CentralWidget {
    background-color: #07090E;
    color: #F8FAFC;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Sidebar Container */
QWidget#SidebarContainer {
    background-color: #0B0E17;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Sidebar Navigation Buttons */
QPushButton.NavBtn {
    background-color: transparent;
    color: #94A3B8;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13.5px;
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

/* Glass Cards */
QFrame.GlassCard {
    background-color: rgba(18, 24, 38, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 18px;
}

QFrame.GlassCard:hover {
    border: 1px solid rgba(0, 255, 170, 0.25);
    background-color: rgba(24, 32, 50, 0.85);
}

/* Input Fields */
QLineEdit, QComboBox {
    background-color: rgba(14, 18, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 8px 14px;
    color: #F8FAFC;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00FFAA;
    background-color: rgba(18, 24, 38, 0.95);
}

/* Buttons */
QPushButton.ActionBtn {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton.ActionBtn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: #FFFFFF;
}

QPushButton.PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00D4FF);
    color: #0B0E14;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton.PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D75FF, stop:1 #1CE0FF);
}

/* Scroll Area & Scrollbars */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #0B0E17;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #232D42;
    border-radius: 3px;
    min-height: 25px;
}

QScrollBar::handle:vertical:hover {
    background: #384766;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Progress Bar */
QProgressBar {
    background-color: #141A28;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-weight: bold;
    height: 16px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6C63FF, stop:1 #00FFAA);
    border-radius: 5px;
}
"""


def apply_theonix_style(app: QApplication):
    """Applies the standard Theonix OS style and theme to the application."""
    app.setStyle("Fusion")
    app.setStyleSheet(THEONIX_THEME_QSS)


class GlassCard(QFrame):
    """Reusable Acrylic Glass Card Container."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "GlassCard")


class NavButton(QPushButton):
    """Sleek sidebar navigation button with accent indicator."""
    def __init__(self, text: str, icon_str: str = "", parent=None):
        super().__init__(f"{icon_str}  {text}" if icon_str else text, parent)
        self.setProperty("class", "NavBtn")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class Badge(QLabel):
    """Status and category pill badge."""
    def __init__(self, text: str, variant: str = "cyan", parent=None):
        super().__init__(text, parent)
        colors = {
            "cyan": ("rgba(0, 255, 170, 0.15)", "#00FFAA"),
            "blue": ("rgba(0, 212, 255, 0.15)", "#00D4FF"),
            "indigo": ("rgba(108, 99, 255, 0.2)", "#A78BFA"),
            "green": ("rgba(39, 201, 63, 0.15)", "#27C93F"),
            "yellow": ("rgba(255, 189, 46, 0.15)", "#FFBD2E"),
            "red": ("rgba(255, 95, 86, 0.15)", "#FF5F56"),
        }
        bg, fg = colors.get(variant, colors["cyan"])
        self.setStyleSheet(f"background-color: {bg}; color: {fg}; border-radius: 5px; padding: 2px 7px; font-size: 11px; font-weight: bold;")


class TelemetryBar(QWidget):
    """Live metric bar with label, value, and progress fill."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 13px; width: 100px;")
        
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)

        self.val_lbl = QLabel("0%")
        self.val_lbl.setStyleSheet("color: #00FFAA; font-weight: bold; width: 50px;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.bar, 1)
        layout.addWidget(self.val_lbl)

    def set_value(self, val: int, label_text: str = None):
        self.bar.setValue(val)
        self.val_lbl.setText(label_text if label_text else f"{val}%")


class SearchBar(QLineEdit):
    """Glassmorphic search bar with clear button."""
    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.setStyleSheet("""
            background-color: rgba(14, 18, 28, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9px;
            padding: 8px 16px;
            color: #FFFFFF;
            font-size: 13.5px;
        """)


class QuickLookDialog(QDialog):
    """Spacebar Quick Look modal for instant file previews (Images, Text, Code, PDF)."""
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Quick Look — {os.path.basename(file_path)}")
        self.setMinimumSize(640, 480)
        self.resize(720, 520)
        self.setStyleSheet(THEONIX_THEME_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title = QLabel(f"📄  {os.path.basename(file_path)}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        
        sz = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        sz_str = f"{sz/1024:.1f} KB" if sz < 1024**2 else f"{sz/(1024**2):.1f} MB"
        sz_lbl = QLabel(f"Size: {sz_str}")
        sz_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(sz_lbl)
        layout.addLayout(hdr)

        # Preview Body
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp", ".gif"]:
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                img_lbl.setPixmap(pixmap.scaled(660, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            layout.addWidget(img_lbl, 1)
        else:
            # Text / Code Preview
            txt_box = QTextEdit()
            txt_box.setReadOnly(True)
            txt_box.setStyleSheet("background-color: #0B0E14; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; color: #E2E8F0; font-family: monospace; font-size: 12.5px; padding: 12px;")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(15000)
                    txt_box.setPlainText(content)
            except Exception as e:
                txt_box.setPlainText(f"Could not load preview: {e}")
            layout.addWidget(txt_box, 1)

        # Bottom Close Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close (Space / Esc)")
        close_btn.setProperty("class", "ActionBtn")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Escape):
            self.accept()
        else:
            super().keyPressEvent(event)
