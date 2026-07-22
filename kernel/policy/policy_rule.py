from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """
    Defines a policy rule for a capability intent.
    """

    intent: str
    allowed: bool = True
    requires_approval: bool = False
    reason: str = "Allowed by policy."
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate and normalize the policy rule."""
        normalized_intent = self.intent.strip().lower()
        if not normalized_intent:
            raise ValueError("Policy intent cannot be empty.")

        object.__setattr__(self, "intent", normalized_intent)

        metadata = self.metadata or {}
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(metadata)),
        )

    @property
    def denied(self) -> bool:
        """Return True when this rule denies the request."""
        return not self.allowed

    @property
    def approval_required(self) -> bool:
        """Return True when approval is required before execution."""
        return self.requires_approval

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "metadata": dict(self.metadata or {}),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PolicyRule":
        """Create a PolicyRule from a dictionary."""
        return cls(
            intent=str(data["intent"]),
            allowed=bool(data.get("allowed", True)),
            requires_approval=bool(data.get("requires_approval", False)),
            reason=str(data.get("reason", "Allowed by policy.")),
            metadata=dict(data.get("metadata", {})),
        )