"""Recovery manager for the Kernel Recovery Engine."""

from __future__ import annotations

from typing import Any

from kernel.recovery.recovery_action import RecoveryAction
from kernel.recovery.recovery_policy import RecoveryPolicy
from kernel.recovery.recovery_result import RecoveryResult


class RecoveryManager:
    """Coordinates recovery decisions using a recovery policy."""

    def __init__(self, policy: RecoveryPolicy | None = None) -> None:
        self._policy = policy or RecoveryPolicy()

    @property
    def policy(self) -> RecoveryPolicy:
        """Return the active recovery policy."""
        return self._policy

    def policy_info(self) -> dict[str, Any]:
        """Return metadata describing the active recovery policy."""
        return {
            "policy": type(self._policy).__name__,
        }

    def recover(self, attempt: int, message: str = "") -> RecoveryResult:
        """Determine and return the recovery result for a failed operation."""
        action = self._policy.next_action(attempt)
        success = action is not RecoveryAction.ABORT
        return RecoveryResult(
            success=success,
            action=action,
            message=message,
        )

    def can_retry(self, attempt: int) -> bool:
        """Return whether the next recovery action is a retry."""
        return self._policy.next_action(attempt) is RecoveryAction.RETRY

    async def health_check(self) -> bool:
        """Return True while the recovery manager is operational."""
        return True

    async def manager_info(self) -> dict[str, Any]:
        """Return runtime metadata for the recovery manager."""
        return {
            "healthy": await self.health_check(),
            "policy": type(self._policy).__name__,
        }