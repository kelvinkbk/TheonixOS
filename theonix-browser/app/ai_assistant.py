"""
Theonix Browser — Ask Theonix AI Assistant (THAID).
Provides 3-Level Browser & Page Intelligence:
  Level 1: Page Intelligence (Summaries, Code Extraction, Translation, Selected Text, Tables)
  Level 2: Browser State Intelligence (Current URL, Title, Open Tabs, Multi-tab Comparisons)
  Level 3: Browser Action Automation (Navigation, Tab Management, Element Clicking, Form Typing)
"""

import os
from typing import List, Dict, Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGridLayout, QFrame, QComboBox
)

from theonix_core import (
    Badge, AIService, ContextManager, BrowserContext, ModelRouter,
    BrowserService, tools
)


class AIWorkerThread(QThread):
    chunk_received = pyqtSignal(str)
    action_requested = pyqtSignal(str, dict)
    finished = pyqtSignal()

    def __init__(self, prompt: str, browser_ctx: Optional[BrowserContext] = None, model_preference: str = "auto"):
        super().__init__()
        self.prompt = prompt
        self.browser_ctx = browser_ctx
        self.model_preference = model_preference

    def run(self):
        # 1. Build multi-layer prompt using ContextManager
        messages = ContextManager.build_prompt(
            user_prompt=self.prompt,
            browser_ctx=self.browser_ctx,
            system_instructions=(
                "You are THAID, the native intelligence engine built into Theonix Browser and Theonix OS. "
                "You have full context over the current webpage, tabs, and browser state. "
                "Provide accurate, actionable, clean answers with Markdown formatting."
            )
        )

        # 2. Intelligent Model Routing
        ctx_len = len(self.browser_ctx.page_text) if (self.browser_ctx and self.browser_ctx.page_text) else 0
        selected_model = ModelRouter.select_model(
            prompt=self.prompt,
            context_len=ctx_len,
            user_preference=self.model_preference
        )

        try:
            for token in AIService.stream_chat(messages, model_id=selected_model):
                self.chunk_received.emit(token)
        except Exception as e:
            self.chunk_received.emit(f"\n[THAID Error: {e}]\n")
        self.finished.emit()


class AskTheonixDrawer(QFrame):
    def __init__(self, get_active_view_callback, parent=None):
        super().__init__(parent)
        self.get_active_view = get_active_view_callback
        self.setObjectName("AISidebar")
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("✨ Ask Theonix")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #00FFAA;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.model_selector = QComboBox()
        self.model_selector.addItems(["Auto Route", "⚡ Fast (1.5B)", "🧠 Quality (4B)"])
        self.model_selector.setStyleSheet(
            "background-color: #121826; color: #94A3B8; border: 1px solid #1E2638; "
            "border-radius: 6px; font-size: 11px; padding: 2px 6px;"
        )
        hdr.addWidget(self.model_selector)
        layout.addLayout(hdr)

        # Quick action pills (Level 1: Page Intelligence)
        pills_grid = QGridLayout()
        pills_grid.setSpacing(6)

        p1 = QPushButton("📝 Summarize Page")
        p1.setProperty("class", "ActionBtn")
        p1.setStyleSheet("font-size: 11.5px; padding: 6px;")
        p1.clicked.connect(self._summarize_page)

        p2 = QPushButton("💻 Extract Code")
        p2.setProperty("class", "ActionBtn")
        p2.setStyleSheet("font-size: 11.5px; padding: 6px;")
        p2.clicked.connect(self._extract_code)

        p3 = QPushButton("📊 Extract Tables")
        p3.setProperty("class", "ActionBtn")
        p3.setStyleSheet("font-size: 11.5px; padding: 6px;")
        p3.clicked.connect(self._extract_tables)

        p4 = QPushButton("🔍 Explain Selection")
        p4.setProperty("class", "ActionBtn")
        p4.setStyleSheet("font-size: 11.5px; padding: 6px;")
        p4.clicked.connect(self._explain_selection)

        pills_grid.addWidget(p1, 0, 0)
        pills_grid.addWidget(p2, 0, 1)
        pills_grid.addWidget(p3, 1, 0)
        pills_grid.addWidget(p4, 1, 1)
        layout.addLayout(pills_grid)

        # Chat Log
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_log.setStyleSheet(
            "background-color: rgba(14, 18, 28, 0.9); border: 1px solid rgba(255,255,255,0.08); "
            "border-radius: 10px; color: #F8FAFC; padding: 10px; font-size: 12.5px; line-height: 1.5;"
        )
        self.chat_log.setPlaceholderText("Ask THAID to analyze this page, compare open tabs, or execute browser actions...")
        layout.addWidget(self.chat_log)

        # Prompt Input
        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask THAID or command browser...")
        self.input_field.returnPressed.connect(self._send_custom_prompt)

        send_btn = QPushButton("Ask")
        send_btn.setProperty("class", "PrimaryBtn")
        send_btn.clicked.connect(self._send_custom_prompt)

        input_row.addWidget(self.input_field)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

        self.worker = None

    def _get_model_pref(self) -> str:
        idx = self.model_selector.currentIndex()
        if idx == 1:
            return "1.5b"
        elif idx == 2:
            return "4b"
        return "auto"

    def _summarize_page(self):
        self._dispatch_with_context("Please summarize the main content and key takeaways of this webpage concisely.")

    def _extract_code(self):
        self._dispatch_with_context("Extract all code snippets, terminal commands, scripts, and syntax examples from this page.")

    def _extract_tables(self):
        self._dispatch_with_context("Extract all tabular data, matrices, and structured comparisons from this page into Markdown tables.")

    def _explain_selection(self):
        view = self.get_active_view()
        if view and hasattr(view, "extract_selected_text"):
            def _on_selection(sel_text: str):
                if sel_text.strip():
                    self._dispatch_with_context("Explain the selected text simply and provide context.", selected_override=sel_text)
                else:
                    self.chat_log.append("💡 <i>Please select some text on the webpage first, then click Explain Selection.</i>\n")
            view.extract_selected_text(_on_selection)

    def _send_custom_prompt(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._dispatch_with_context(text)

    def _dispatch_with_context(self, prompt: str, selected_override: str = ""):
        p_lower = prompt.strip().lower()

        # Level 3: Direct Browser Actions safely executed on Main GUI Thread
        if p_lower.startswith("open tab") or p_lower.startswith("new tab"):
            self.chat_log.append(f"<b>You:</b> {prompt}\n")
            parts = prompt.split(" ", 2)
            target = parts[2] if len(parts) > 2 else "theonix://newtab"
            target = target.strip("'\"<>` ")
            if not target.startswith(("http://", "https://", "theonix://")):
                target = "https://" + target
            BrowserService.open_tab(target)
            self.chat_log.append(f"<b>THAID:</b> ✓ Opened new tab: `{target}`\n")
            return

        if p_lower.startswith("scroll down"):
            self.chat_log.append(f"<b>You:</b> {prompt}\n")
            BrowserService.scroll("down", 600)
            self.chat_log.append("<b>THAID:</b> ✓ Scrolled down.\n")
            return

        if p_lower.startswith("scroll up"):
            self.chat_log.append(f"<b>You:</b> {prompt}\n")
            BrowserService.scroll("up", 600)
            self.chat_log.append("<b>THAID:</b> ✓ Scrolled up.\n")
            return

        if p_lower.startswith("close tab"):
            self.chat_log.append(f"<b>You:</b> {prompt}\n")
            BrowserService.close_current_tab()
            self.chat_log.append("<b>THAID:</b> ✓ Closed tab.\n")
            return

        self.chat_log.append(f"<b>You:</b> {prompt}\n")
        self.chat_log.append("<b>THAID:</b> <i>Thinking...</i>\n")

        view = self.get_active_view()
        url = view.property("current_url") if view else ""
        title = ""
        if hasattr(self.parent(), "tab_bar") and self.parent().tab_bar:
            title = self.parent().tab_bar.tabText(self.parent().tab_bar.currentIndex())

        # Collect open tabs list for Level 2 Browser State Intelligence
        open_tabs = []
        if hasattr(self.parent(), "tab_bar") and self.parent().tab_bar:
            for i in range(self.parent().tab_bar.count()):
                open_tabs.append({"title": self.parent().tab_bar.tabText(i)})

        if view and hasattr(view, "extract_page_text"):
            def _on_extracted(page_text: str):
                ctx = BrowserContext(
                    url=url or "",
                    title=title or "",
                    selected_text=selected_override,
                    page_text=page_text or "",
                    open_tabs=open_tabs
                )
                self._start_worker(prompt, ctx)
            view.extract_page_text(_on_extracted)
        else:
            ctx = BrowserContext(url=url or "", title=title or "", open_tabs=open_tabs)
            self._start_worker(prompt, ctx)

    def _start_worker(self, prompt: str, ctx: BrowserContext):
        self.worker = AIWorkerThread(prompt, browser_ctx=ctx, model_preference=self._get_model_pref())
        self.worker.chunk_received.connect(lambda c: self.chat_log.append(c))
        self.worker.action_requested.connect(self._handle_async_action)
        self.worker.start()

    @pyqtSlot(str, dict)
    def _handle_async_action(self, tool_name: str, params: dict):
        tools.execute(tool_name, **params)
