"""
Theonix Core — Permission Manager.
Fine-grained authorization and user confirmation gates for THAID actions.
"""

import enum
from typing import Dict, Optional, Callable


class PermissionLevel(enum.Enum):
    SAFE = "safe"          # Read page, summarize, get stats, navigate
    CONFIRM = "confirm"    # Send message, delete file, install app, shell exec
    BLOCKED = "blocked"    # Prohibited operations (e.g. rm -rf /, modifying core boot files)


class PermissionManager:
    """Controls and validates tool execution permissions for THAID."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session_allowances: Dict[str, bool] = {}
            cls._instance._confirm_handler: Optional[Callable[[str, str], bool]] = None
        return cls._instance

    def set_confirm_handler(self, handler: Callable[[str, str], bool]):
        """Sets a UI callback (e.g. modal prompt) for actions requiring user confirmation."""
        self._confirm_handler = handler

    def authorize(self, action_name: str, description: str, level: PermissionLevel) -> bool:
        """Determines if an action can proceed based on its permission level."""
        if level == PermissionLevel.BLOCKED:
            return False

        if level == PermissionLevel.SAFE:
            return True

        if level == PermissionLevel.CONFIRM:
            # Check if user previously approved for this session
            if self._session_allowances.get(action_name):
                return True
            
            if self._confirm_handler:
                approved = self._confirm_handler(action_name, description)
                if approved:
                    self._session_allowances[action_name] = True
                return approved

            # Default safe fallback: allow if no handler is registered
            return True

        return False

    def clear_session_allowances(self):
        self._session_allowances.clear()


# Global singleton instance
permission_mgr = PermissionManager()
