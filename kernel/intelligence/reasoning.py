"""Reasoning model for the Kernel Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Reasoning:
    """Structured output of the Reasoning Engine.

    A Reasoning object describes which capability should handle an
    intent, how important the work is, and whether the user must
    confirm before anything is executed. It is immutable so downstream
    layers can rely on a stable, deterministic decision.
    """

    intent_name: str
    capability: str
    explanation: str
    priority: str
    requires_confirmation: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the reasoning."""
        return {
            "intent_name": self.intent_name,
            "capability": self.capability,
            "explanation": self.explanation,
            "priority": self.priority,
            "requires_confirmation": self.requires_confirmation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Reasoning:
        """Reconstruct reasoning from its serialized form."""
        return cls(
            intent_name=data["intent_name"],
            capability=data["capability"],
            explanation=data["explanation"],
            priority=data["priority"],
            requires_confirmation=data["requires_confirmation"],
        )
