"""Tool registry for the JARVIS Kernel.

The ToolRegistry is responsible for registering, validating, and invoking
tools through the framework-independent Tool interface.
"""

from __future__ import annotations

from typing import Any

from kernel.interfaces.tool import Tool


class ToolRegistry:
    """Central registry for all Kernel tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> bool:
        """Remove a tool."""

        return self._tools.pop(tool_name, None) is not None

    def get(self, tool_name: str) -> Tool:
        """Return a registered tool."""

        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_name}") from exc

    def list_tools(self) -> list[str]:
        """Return all registered tool names."""

        return sorted(self._tools.keys())

    async def invoke(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:
        """Validate and invoke a tool."""

        tool = self.get(tool_name)

        valid = await tool.validate(**kwargs)
        if not valid:
            raise ValueError(
                f"Validation failed for tool '{tool_name}'."
            )

        return await tool.invoke(**kwargs)

    async def health_check(self) -> bool:
        """Return overall registry health."""

        # An empty registry is considered healthy during bootstrap.
        if not self._tools:
            return True

        return all(
            await tool.health_check()
            for tool in self._tools.values()
        )

    def exists(self, tool_name: str) -> bool:
        """Return True if a tool is registered."""

        return tool_name in self._tools

    def clear(self) -> None:
        """Remove all registered tools."""

        self._tools.clear()

    @property
    def count(self) -> int:
        """Return the number of registered tools."""

        return len(self._tools)