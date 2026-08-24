#!/usr/bin/env python3
"""
Theonix Browser — Entry point.
Native AI-Augmented Web Browser for Theonix OS.
"""

import os
import sys

# Ensure local app directory and theonix-core are on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "theonix-core")))

from PyQt6.QtWidgets import QApplication
from app.browser_window import TheonixBrowserWindow, BROWSER_THEME_QSS


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(BROWSER_THEME_QSS)
    win = TheonixBrowserWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
