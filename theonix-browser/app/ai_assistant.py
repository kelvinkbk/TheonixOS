"""
Theonix Browser — Ask Theonix AI Assistant (THAID).
Provides interactive page summarization, question answering, code extraction, and translation.
"""

import subprocess
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGridLayout, QFrame
)

from theonix_core import Badge, AIService


class AIWorkerThread(QThread):
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, prompt: str, context: str = "", model_id: str = "1.5b"):
        super().__init__()
        self.prompt = prompt
        self.context = context
        self.model_id = model_id

    def run(self):
        messages = []
        system_prompt = (
            "You are THAID, the intelligent native AI assistant built into Theonix OS. "
            "Help the user analyze, summarize, code, or extract insights cleanly and accurately."
        )

        user_content = self.prompt
        if self.context:
            user_content = f"Webpage Context:\n```\n{self.context[:6000]}\n```\n\nUser Question/Request:\n{self.prompt}"

        messages.append({"role": "user", "content": user_content})

        try:
            for token in AIService.stream_chat(messages, model_id=self.model_id, system_prompt=system_prompt):
                self.chunk_received.emit(token)
        except Exception as e:
            self.chunk_received.emit(f"\n[THAID Connection Error: {e}]\n")
        self.finished.emit()


class AskTheonixDrawer(QFrame):
    def __init__(self, get_active_view_callback, parent=None):
        super().__init__(parent)
        self.get_active_view = get_active_view_callback
        self.setObjectName("AISidebar")
        self.setFixedWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🤖 Ask Theonix")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00FFAA;")
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(Badge("THAID ONLINE", "cyan"))
        layout.addLayout(hdr)

        # Quick action pills
        pills_grid = QGridLayout()
        pills_grid.setSpacing(6)

        p1 = QPushButton("📝 Summarize Page")
        p1.setProperty("class", "ActionBtn")
        p1.clicked.connect(self._summarize_page)

        p2 = QPushButton("💻 Extract Code")
        p2.setProperty("class", "ActionBtn")
        p2.clicked.connect(self._extract_code)

        p3 = QPushButton("🔍 Explain Simply")
        p3.setProperty("class", "ActionBtn")
        p3.clicked.connect(self._explain_simply)

        p4 = QPushButton("🌐 Translate")
        p4.setProperty("class", "ActionBtn")
        p4.clicked.connect(self._translate_page)

        pills_grid.addWidget(p1, 0, 0)
        pills_grid.addWidget(p2, 0, 1)
        pills_grid.addWidget(p3, 1, 0)
        pills_grid.addWidget(p4, 1, 1)
        layout.addLayout(pills_grid)

        # Chat Log
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setStyleSheet(
            "background-color: rgba(14, 18, 28, 0.85); border: 1px solid rgba(255,255,255,0.08); "
            "border-radius: 10px; color: #F8FAFC; padding: 10px; font-size: 13px;"
        )
        self.chat_log.setPlaceholderText("Ask THAID about this page or any topic...")
        layout.addWidget(self.chat_log)

        # Prompt Input
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask THAID...")
        self.input_field.returnPressed.connect(self._send_custom_prompt)

        send_btn = QPushButton("Ask")
        send_btn.setProperty("class", "PrimaryBtn")
        send_btn.clicked.connect(self._send_custom_prompt)

        input_row.addWidget(self.input_field)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        self.worker = None

    def _summarize_page(self):
        self._dispatch_with_page_context("Please summarize the main content and key takeaways of this webpage concisely.")

    def _extract_code(self):
        self._dispatch_with_page_context("Extract all code snippets, shell commands, scripts, and syntax examples from this page.")

    def _explain_simply(self):
        self._dispatch_with_page_context("Explain the core ideas on this page in simple terms with bullet points.")

    def _translate_page(self):
        self._dispatch_with_page_context("Translate the key content of this page to clear, fluent English.")

    def _send_custom_prompt(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._dispatch_with_page_context(text)

    def _dispatch_with_page_context(self, prompt: str):
        self.chat_log.append(f"<b>You:</b> {prompt}\n")
        self.chat_log.append("<b>THAID:</b> <i>Analyzing page & thinking...</i>\n")

        view = self.get_active_view()
        if view and hasattr(view, "extract_page_text"):
            def _on_extracted(page_text: str):
                self.worker = AIWorkerThread(prompt, context=page_text or "")
                self.worker.chunk_received.connect(lambda c: self.chat_log.append(c))
                self.worker.start()
            view.extract_page_text(_on_extracted)
        else:
            self.worker = AIWorkerThread(prompt, context="")
            self.worker.chunk_received.connect(lambda c: self.chat_log.append(c))
            self.worker.start()
