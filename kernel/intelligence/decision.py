"""Decision model for the Kernel Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

EXECUTE: Final[str] = "execute"
ASK_CONFIRMATION: Final[str] = "ask_confirmation"
ASK_CLARIFICATION: Final[str] = "ask_clarification"
REJECT: Final[str] = "reject"
DEFER: Final[str] = "defer"
NOOP: Final[str] = "noop"

VALID_ACTIONS: Final[frozenset[str]] = frozenset(
    {EXECUTE, ASK_CONFIRMATION, ASK_CLARIFICATION, REJECT, DEFER, NOOP}
)


@dataclass(frozen=True, slots=True)
class Decision:
    """Final executable choice produced by the Decision Engine.

    A Decision describes what the Kernel should do next after an Intent
    has been classified and reasoned about. It is immutable so the
    Executive Engine can rely on a stable, deterministic choice.
    """

    action: str
    confidence: float
    requires_confirmation: bool
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the decision."""
        return {
            "action": self.action,
            "confidence": self.confidence,
            "requires_confirmation": self.requires_confirmation,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decision:
        """Reconstruct a decision from its serialized form."""
        return cls(
            action=data["action"],
            confidence=data["confidence"],
            requires_confirmation=data["requires_confirmation"],
            explanation=data["explanation"],
            metadata=dict(data.get("metadata", {})),
        )
