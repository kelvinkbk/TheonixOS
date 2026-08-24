"""
Theonix Core — Browser Service.
Controls WebEngine automation, DOM extraction, and browser actions for THAID.
"""

from typing import Callable, Optional, Dict, Any, List
from .tools import Tool, tools
from .permissions import PermissionLevel
from .events import bus


class BrowserService:
    """Manages automation and intelligence operations on the browser instance."""

    _active_window = None

    @classmethod
    def set_active_window(cls, window):
        cls._active_window = window

    @classmethod
    def navigate(cls, url: str) -> bool:
        if cls._active_window and hasattr(cls._active_window, "_navigate_to"):
            cls._active_window._navigate_to(url)
            bus.emit("browser.navigated", {"url": url})
            return True
        return False

    @classmethod
    def open_tab(cls, url: str = "theonix://newtab", title: str = "New Tab") -> bool:
        if cls._active_window and hasattr(cls._active_window, "add_tab"):
            cls._active_window.add_tab(url, title)
            bus.emit("browser.tab_opened", {"url": url})
            return True
        return False

    @classmethod
    def close_current_tab(cls) -> bool:
        if cls._active_window and hasattr(cls._active_window, "tab_bar"):
            idx = cls._active_window.tab_bar.currentIndex()
            cls._active_window._close_tab(idx)
            return True
        return False

    @classmethod
    def get_current_url(cls) -> str:
        if cls._active_window and hasattr(cls._active_window, "url_bar"):
            return cls._active_window.url_bar.text().strip()
        return ""

    @classmethod
    def execute_script(cls, js_code: str, callback: Optional[Callable[[Any], None]] = None):
        if not cls._active_window:
            return
        view = cls._active_window._get_current_view()
        if view and hasattr(view, "page") and view.page():
            view.page().runJavaScript(js_code, callback or (lambda res: None))

    @classmethod
    def click_element(cls, selector: str):
        """Clicks an element matching CSS selector in the active web page."""
        js = f"""
        (function() {{
            let el = document.querySelector('{selector}');
            if (el) {{ el.click(); return true; }}
            return false;
        }})();
        """
        cls.execute_script(js)

    @classmethod
    def type_into_element(cls, selector: str, text: str):
        """Types text into an input or textarea element."""
        clean_text = text.replace("'", "\\'")
        js = f"""
        (function() {{
            let el = document.querySelector('{selector}');
            if (el) {{
                el.focus();
                el.value = '{clean_text}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }})();
        """
        cls.execute_script(js)

    @classmethod
    def scroll(cls, direction: str = "down", amount: int = 500):
        y = amount if direction == "down" else -amount
        js = f"window.scrollBy({{ top: {y}, behavior: 'smooth' }});"
        cls.execute_script(js)


# ---- Register Default Browser Tools in ToolRegistry ----
tools.register(Tool(
    name="browser.navigate",
    description="Navigate the browser to a specific URL",
    parameters={"url": "string"},
    handler=lambda url: BrowserService.navigate(url),
    permission_level=PermissionLevel.SAFE
))

tools.register(Tool(
    name="browser.open_tab",
    description="Open a new browser tab with given URL",
    parameters={"url": "string"},
    handler=lambda url="theonix://newtab": BrowserService.open_tab(url),
    permission_level=PermissionLevel.SAFE
))

tools.register(Tool(
    name="browser.click",
    description="Click a button or link matching a CSS selector",
    parameters={"selector": "string"},
    handler=lambda selector: BrowserService.click_element(selector),
    permission_level=PermissionLevel.SAFE
))

tools.register(Tool(
    name="browser.type",
    description="Type text into a search bar or input field",
    parameters={"selector": "string", "text": "string"},
    handler=lambda selector, text: BrowserService.type_into_element(selector, text),
    permission_level=PermissionLevel.SAFE
))

tools.register(Tool(
    name="browser.scroll",
    description="Scroll the active webpage up or down",
    parameters={"direction": "string"},
    handler=lambda direction="down": BrowserService.scroll(direction),
    permission_level=PermissionLevel.SAFE
))
