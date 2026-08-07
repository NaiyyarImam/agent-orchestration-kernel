"""Execution model for the Kernel Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

PENDING: Final[str] = "PENDING"
RUNNING: Final[str] = "RUNNING"
COMPLETED: Final[str] = "COMPLETED"
FAILED: Final[str] = "FAILED"
CANCELLED: Final[str] = "CANCELLED"

EXECUTION_STATUSES: Final[frozenset[str]] = frozenset(
    {PENDING, RUNNING, COMPLETED, FAILED, CANCELLED}
)

DEFAULT_STATUS: Final[str] = PENDING


@dataclass(frozen=True, slots=True)
class Execution:
    """Deterministic execution record produced by the Execution Engine.

    An Execution captures the outcome of running a Plan through the
    Kernel. It is immutable so the Executive Engine can rely on a
    stable, deterministic record of what happened.
    """

    execution_id: str
    plan_id: str
    action: str
    status: str = DEFAULT_STATUS
    success: bool = False
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the execution."""
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "action": self.action,
            "status": self.status,
            "success": self.success,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Execution:
        """Reconstruct an execution from its serialized form."""
        return cls(
            execution_id=data["execution_id"],
            plan_id=data["plan_id"],
            action=data["action"],
            status=data.get("status", DEFAULT_STATUS),
            success=data.get("success", False),
            confidence=data.get("confidence", 0.0),
            metadata=dict(data.get("metadata", {})),
        )
