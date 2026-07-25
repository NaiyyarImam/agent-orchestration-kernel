

"""Recovery manager for the Kernel Recovery Engine."""

from __future__ import annotations

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

    def recover(self, attempt: int, message: str = "") -> RecoveryResult:
        """Determine and return the recovery result for a failed operation."""
        action = self._policy.next_action(attempt)
        success = action is not RecoveryAction.ABORT
        return RecoveryResult(
            success=success,
            action=action,
            message=message,
        )

    async def health_check(self) -> bool:
        """Return True while the recovery manager is operational."""
        return True