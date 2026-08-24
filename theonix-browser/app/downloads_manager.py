"""
Theonix Browser — Downloads Manager.
Handles Qt WebEngine download requests, progress monitoring, and Theonix Files integration.
"""

import os
import subprocess
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")


class DownloadItem(QObject):
    progress_changed = pyqtSignal(int, int) # received_bytes, total_bytes
    status_changed = pyqtSignal(str)       # "downloading", "completed", "cancelled", "interrupted"

    def __init__(self, download_request, save_path: str):
        super().__init__()
        self.request = download_request
        self.save_path = save_path
        self.filename = os.path.basename(save_path)
        self.received_bytes = 0
        self.total_bytes = 0
        self.status = "downloading"

        if hasattr(self.request, "downloadProgress"):
            self.request.downloadProgress.connect(self._on_progress)
        if hasattr(self.request, "stateChanged"):
            self.request.stateChanged.connect(self._on_state_changed)

    def _on_progress(self, received: int, total: int):
        self.received_bytes = received
        self.total_bytes = total
        self.progress_changed.emit(received, total)

    def _on_state_changed(self, state):
        # QWebEngineDownloadRequest.DownloadState
        # 0: Uninitialized, 1: InProgress, 2: Completed, 3: Cancelled, 4: Interrupted
        if state == 2:
            self.status = "completed"
        elif state == 3:
            self.status = "cancelled"
        elif state == 4:
            self.status = "interrupted"
        self.status_changed.emit(self.status)

    def cancel(self):
        if hasattr(self.request, "cancel"):
            self.request.cancel()
            self.status = "cancelled"
            self.status_changed.emit("cancelled")

    def open_file(self):
        if os.path.exists(self.save_path):
            subprocess.Popen(["xdg-open", self.save_path])

    def show_in_files(self):
        folder = os.path.dirname(self.save_path)
        if os.path.exists(folder):
            subprocess.Popen(["theonix-files", folder], stderr=subprocess.DEVNULL)
            # fallback to xdg-open if theonix-files is not installed
            subprocess.Popen(["xdg-open", folder], stderr=subprocess.DEVNULL)


class DownloadsManager(QObject):
    download_started = pyqtSignal(DownloadItem)

    def __init__(self, download_dir: str = DEFAULT_DOWNLOAD_DIR):
        super().__init__()
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.downloads: List[DownloadItem] = []

    def handle_download_request(self, download_request):
        suggested_name = download_request.downloadFileName() if hasattr(download_request, "downloadFileName") else "download"
        if hasattr(download_request, "suggestedFileName"):
            suggested_name = download_request.suggestedFileName() or suggested_name

        save_path = os.path.join(self.download_dir, suggested_name)
        
        # Ensure unique name if exists
        base, ext = os.path.splitext(save_path)
        counter = 1
        while os.path.exists(save_path):
            save_path = f"{base}_{counter}{ext}"
            counter += 1

        if hasattr(download_request, "setDownloadDirectory"):
            download_request.setDownloadDirectory(os.path.dirname(save_path))
            download_request.setDownloadFileName(os.path.basename(save_path))
        elif hasattr(download_request, "setSavePageFormat"):
            pass

        if hasattr(download_request, "accept"):
            download_request.accept()

        item = DownloadItem(download_request, save_path)
        self.downloads.insert(0, item)
        self.download_started.emit(item)
        return item
