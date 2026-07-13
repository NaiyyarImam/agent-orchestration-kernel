

"""Abstract interface for the JARVIS Kernel security policy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SecurityPolicy(ABC):
    """Framework-independent security and permission contract.

    Every high-impact action performed by the Kernel must be validated
    through this interface before execution.
    """

    @abstractmethod
    async def authorize(
        self,
        subject: str,
        action: str,
        resource: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Return True if the requested action is permitted."""

    @abstractmethod
    async def sandbox_required(
        self,
        action: str,
        resource: str,
    ) -> bool:
        """Return True if the action must execute inside a sandbox."""

    @abstractmethod
    async def audit(
        self,
        event: str,
        details: dict[str, Any],
    ) -> None:
        """Record a security-relevant event for auditing."""

    @abstractmethod
    async def validate_tool(
        self,
        tool_name: str,
    ) -> bool:
        """Return True if the tool is approved for execution."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the security policy service is operational."""