

"""Recovery result returned by the Kernel Recovery Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from kernel.recovery.recovery_action import RecoveryAction


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    """Represents the outcome of a recovery attempt."""

    success: bool
    action: RecoveryAction
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, object]:
        """Serialize the recovery result to a dictionary."""
        return {
            "success": self.success,
            "action": self.action.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RecoveryResult":
        """Create a RecoveryResult from a serialized dictionary."""
        return cls(
            success=bool(data["success"]),
            action=RecoveryAction(str(data["action"])),
            message=str(data.get("message", "")),
            timestamp=datetime.fromisoformat(str(data["timestamp"])),
        )