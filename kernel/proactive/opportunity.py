"""Opportunity model for the Proactive Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class OpportunitySeverity(str, Enum):
    """Severity assigned to a detected opportunity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Opportunity:
    """Represents an opportunity detected by the Proactive Intelligence Engine."""

    title: str
    description: str
    severity: OpportunitySeverity = OpportunitySeverity.MEDIUM
    confidence: float = 1.0
    opportunity_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the opportunity."""
        return {
            "opportunity_id": self.opportunity_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata.copy(),
        }
