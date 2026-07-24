"""Recovery actions supported by the Kernel Recovery Engine."""

from __future__ import annotations

from enum import Enum


class RecoveryAction(str, Enum):
    """Actions the Recovery Engine may take after a failure."""

    RETRY = "retry"
    RESTART = "restart"
    FAILOVER = "failover"
    SKIP = "skip"
    ABORT = "abort"
    IGNORE = "ignore"

    def __str__(self) -> str:
        """Return the action value."""
        return self.value
