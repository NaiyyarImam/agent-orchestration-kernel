"""Plan model for the Kernel Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

EXECUTE: Final[str] = "execute"
REQUEST_CONFIRMATION: Final[str] = "request_confirmation"
DEFER: Final[str] = "defer"
DENY: Final[str] = "deny"
UNKNOWN: Final[str] = "unknown"

PLAN_ACTIONS: Final[frozenset[str]] = frozenset(
    {EXECUTE, REQUEST_CONFIRMATION, DEFER, DENY, UNKNOWN}
)


@dataclass(frozen=True, slots=True)
class Plan:
    """Deterministic execution plan produced by the Planning Engine.

    A Plan converts a Decision into a concrete set of steps the Kernel
    can execute later. It is immutable so the Executive Engine can rely
    on a stable, deterministic plan.
    """

    goal: str
    action: str = UNKNOWN
    priority: int = 0
    requires_confirmation: bool = False
    confidence: float = 0.0
    steps: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the plan."""
        return {
            "goal": self.goal,
            "action": self.action,
            "priority": self.priority,
            "requires_confirmation": self.requires_confirmation,
            "confidence": self.confidence,
            "steps": list(self.steps),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Plan:
        """Reconstruct a plan from its serialized form."""
        return cls(
            goal=data["goal"],
            action=data.get("action", UNKNOWN),
            priority=data.get("priority", 0),
            requires_confirmation=data.get("requires_confirmation", False),
            confidence=data.get("confidence", 0.0),
            steps=tuple(data.get("steps", [])),
            metadata=dict(data.get("metadata", {})),
        )
