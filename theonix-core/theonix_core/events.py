"""
Theonix Core — Event Bus.
OS-wide decoupled Pub/Sub messaging system for Theonix OS and THAID.
"""

from typing import Callable, Dict, List, Any
import threading
import time


class Event:
    def __init__(self, name: str, data: Dict[str, Any] = None):
        self.name = name
        self.data = data or {}
        self.timestamp = time.time()


class EventBus:
    """Singleton event publisher/subscriber for system, browser, and app signals."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
                cls._instance._history: List[Event] = []
            return cls._instance

    def subscribe(self, event_name: str, handler: Callable[[Event], None]):
        """Subscribe to a specific event or '*' for all events."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Event], None]):
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    def emit(self, event_name: str, data: Dict[str, Any] = None):
        """Dispatches an event synchronously to all registered listeners."""
        ev = Event(event_name, data)
        self._history.append(ev)
        if len(self._history) > 100:
            self._history.pop(0)

        handlers = list(self._subscribers.get(event_name, [])) + list(self._subscribers.get("*", []))
        for h in handlers:
            try:
                h(ev)
            except Exception as err:
                print(f"[EventBus] Error handling {event_name}: {err}")

    def get_recent(self, limit: int = 20) -> List[Event]:
        return self._history[-limit:]


# Global singleton instance
bus = EventBus()
