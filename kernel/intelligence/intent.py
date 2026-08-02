"""Intent model for the Kernel Intelligence Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Intent:
    """Structured representation of a classified user request.

    An Intent is the immutable output of the Intent Engine. It describes
    which high-level intent the request maps to, the confidence of that
    classification, and any parameters extracted from the request.
    """

    name: str
    confidence: float
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the intent."""
        return {
            "name": self.name,
            "confidence": self.confidence,
            "parameters": dict(self.parameters),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Intent:
        """Reconstruct an intent from its serialized form."""
        return cls(
            name=data["name"],
            confidence=data["confidence"],
            parameters=dict(data.get("parameters", {})),
        )
