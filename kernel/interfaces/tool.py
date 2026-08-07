

"""Abstract interface for tools exposed to the JARVIS Kernel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Framework-independent contract for executable tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the tool."""

    @abstractmethod
    async def invoke(self, **kwargs: Any) -> Any:
        """Execute the tool with validated arguments."""

    @abstractmethod
    async def validate(self, **kwargs: Any) -> bool:
        """Validate input arguments before execution."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the tool is operational."""

    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """Return the input schema describing the tool interface."""