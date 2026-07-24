

"""Rule model for the Proactive Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class RuleAction(str, Enum):
    """Actions that may be taken when a rule matches."""

    IGNORE = "ignore"
    SUGGEST = "suggest"
    OPPORTUNITY = "opportunity"
    ALERT = "alert"


@dataclass(frozen=True, slots=True)
class ProactiveRule:
    """Represents a rule evaluated against proactive signals."""

    name: str
    description: str
    signal_type: str
    action: RuleAction
    enabled: bool = True
    priority: int = 100
    confidence_threshold: float = 0.5
    rule_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def applies_to(self, signal_type: str, confidence: float) -> bool:
        """Return True if this rule applies to the supplied signal."""
        return (
            self.enabled
            and self.signal_type == signal_type
            and confidence >= self.confidence_threshold
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the rule."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "signal_type": self.signal_type,
            "action": self.action.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "confidence_threshold": self.confidence_threshold,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata.copy(),
        }