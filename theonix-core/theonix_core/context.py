"""
Theonix Core — Context Manager.
Builds, prunes, and formats multi-layer context (System, Browser, Files, App) for THAID.
"""

from typing import Dict, Any, Optional, List


class BrowserContext:
    def __init__(
        self,
        url: str = "",
        title: str = "",
        selected_text: str = "",
        page_text: str = "",
        open_tabs: List[Dict[str, str]] = None
    ):
        self.url = url
        self.title = title
        self.selected_text = selected_text
        self.page_text = page_text
        self.open_tabs = open_tabs or []


class ContextManager:
    """Intelligently structures prompts and prevents context overflow."""

    MAX_PAGE_CHARS = 8000

    @classmethod
    def build_prompt(
        cls,
        user_prompt: str,
        browser_ctx: Optional[BrowserContext] = None,
        file_ctx: Optional[str] = None,
        system_instructions: Optional[str] = None
    ) -> List[Dict[str, str]]:
        messages = []

        # 1. Base System Persona & Tool Capabilities
        base_system = (
            system_instructions or
            "You are THAID, the native, high-performance AI assistant built directly into Theonix OS and Theonix Browser.\n"
            "You have full autonomous understanding of user intents, web pages, and desktop operations.\n\n"
            "AVAILABLE BROWSER & OS TOOLS:\n"
            "• `browser.open_tab(url)`: Opens a new tab with the target URL (e.g. https://archlinux.org, https://youtube.com, https://github.com).\n"
            "• `browser.navigate(url)`: Navigates the current active tab to a URL.\n"
            "• `browser.scroll(direction)`: Scrolls the active page ('down' or 'up').\n"
            "• `browser.close_tab()`: Closes the active tab.\n"
            "• `browser.click(selector)`: Clicks an element matching CSS selector on the page.\n\n"
            "INSTRUCTIONS FOR ACTIONS:\n"
            "When the user asks you in natural language to perform an action (like 'show me arch wiki in a new tab', 'let's go to youtube', 'scroll down', 'close this tab'):\n"
            "Output the action tag in your response:\n"
            "<action>{\"tool\": \"tool_name\", \"params\": {\"param_name\": \"value\"}}</action>\n"
            "Followed by a concise confirmation message.\n\n"
            "When the user is asking questions, requesting code, summaries, translations, or explanations, answer directly in Markdown without tool tags."
        )

        # 2. Inject Context Layers
        context_parts = []
        if browser_ctx:
            if browser_ctx.url:
                context_parts.append(f"• Active URL: {browser_ctx.url}")
            if browser_ctx.title:
                context_parts.append(f"• Page Title: {browser_ctx.title}")
            if browser_ctx.open_tabs:
                tab_list = ", ".join([f"'{t.get('title', 'Tab')}'" for t in browser_ctx.open_tabs[:5]])
                context_parts.append(f"• Open Tabs: {tab_list}")
            if browser_ctx.selected_text:
                context_parts.append(f"• User Selected Text:\n```\n{browser_ctx.selected_text.strip()}\n```")
            elif browser_ctx.page_text:
                clean_text = browser_ctx.page_text[:cls.MAX_PAGE_CHARS].strip()
                context_parts.append(f"• Webpage Content:\n\"\"\"\n{clean_text}\n\"\"\"")

        if file_ctx:
            context_parts.append(f"• File Context:\n```\n{file_ctx[:4000]}\n```")

        if context_parts:
            formatted_context = "\n\n".join(context_parts)
            base_system += f"\n\n--- ENVIRONMENT CONTEXT ---\n{formatted_context}"

        messages.append({"role": "system", "content": base_system})
        messages.append({"role": "user", "content": user_prompt})
        return messages
