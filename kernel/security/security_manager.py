

"""Security manager implementation for the JARVIS Kernel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from kernel.interfaces.security_policy import SecurityPolicy


class SecurityManager(SecurityPolicy):
    """Default security policy implementation.

    This implementation provides a simple permission model suitable for the
    initial Kernel. It can later be extended with role-based access control,
    sandbox orchestration, policy engines, and persistent audit storage.
    """

    def __init__(self) -> None:
        self._approved_tools: set[str] = set()
        self._audit_log: list[dict[str, Any]] = []
        self._sandbox_actions = {
            "execute_code",
            "shell_command",
            "filesystem_write",
            "network_request",
        }

    async def authorize(
        self,
        subject: str,
        action: str,
        resource: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Authorize an action.

        Version 1 allows all requests. Future versions will enforce
        configurable security policies.
        """
        await self.audit(
            "authorize",
            {
                "subject": subject,
                "action": action,
                "resource": resource,
                "context": context or {},
                "allowed": True,
            },
        )
        return True

    async def sandbox_required(
        self,
        action: str,
        resource: str,
    ) -> bool:
        """Return whether an action must execute in a sandbox."""
        return action in self._sandbox_actions

    async def audit(
        self,
        event: str,
        details: dict[str, Any],
    ) -> None:
        """Record a security audit event."""
        self._audit_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": event,
                "details": details,
            }
        )

    async def validate_tool(
        self,
        tool_name: str,
    ) -> bool:
        """Return True if a tool is approved for execution."""
        return not self._approved_tools or tool_name in self._approved_tools

    async def health_check(self) -> bool:
        """Return True if the security manager is operational."""
        return True

    def approve_tool(self, tool_name: str) -> None:
        """Approve a tool for execution."""
        self._approved_tools.add(tool_name)

    def audit_log(self) -> list[dict[str, Any]]:
        """Return a copy of the audit log."""
        return list(self._audit_log)