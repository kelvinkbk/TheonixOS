"""
Theonix Core — Tool Registry & Router.
Extensible, permission-gated tool execution framework for THAID OS and Browser actions.
"""

from typing import Callable, Dict, Any, List, Optional
from .permissions import PermissionLevel, permission_mgr
from .events import bus


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        permission_level: PermissionLevel = PermissionLevel.SAFE
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.permission_level = permission_level

    def execute(self, **kwargs) -> Dict[str, Any]:
        # Validate permission
        if not permission_mgr.authorize(self.name, self.description, self.permission_level):
            return {"success": False, "error": f"Permission denied for tool '{self.name}'."}

        try:
            result = self.handler(**kwargs)
            bus.emit("tool.executed", {"tool": self.name, "params": kwargs, "success": True})
            return {"success": True, "result": result}
        except Exception as e:
            bus.emit("tool.failed", {"tool": self.name, "params": kwargs, "error": str(e)})
            return {"success": False, "error": str(e)}


class ToolRegistry:
    """Central catalog of available system, browser, and app tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Tool] = {}
        return cls._instance

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "permission_level": t.permission_level.value
            }
            for t in self._tools.values()
        ]

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: '{tool_name}'"}
        return tool.execute(**kwargs)


# Global singleton instance
tools = ToolRegistry()
