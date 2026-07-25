

"""Recovery policy definitions for the Kernel Recovery Engine."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.recovery.recovery_action import RecoveryAction


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    """Defines how the Recovery Engine should respond to failures."""

    max_retries: int = 3
    default_action: RecoveryAction = RecoveryAction.RETRY
    retry_delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")

    def next_action(self, attempt: int) -> RecoveryAction:
        """Return the action that should be taken for the given attempt."""
        if attempt < 0:
            raise ValueError("attempt must be non-negative")
        if self.default_action is RecoveryAction.RETRY and attempt >= self.max_retries:
            return RecoveryAction.ABORT
        return self.default_action