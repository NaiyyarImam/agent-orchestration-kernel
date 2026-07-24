

"""Signal model for the Proactive Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class SignalType(str, Enum):
    """Categories of proactive signals."""

    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RESOURCE = "resource"
    WORKFLOW = "workflow"
    USER = "user"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class ProactiveSignal:
    """Represents an observed event that may trigger proactive reasoning."""

    source: str
    signal_type: SignalType
    message: str
    confidence: float = 1.0
    signal_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the signal."""
        return {
            "signal_id": self.signal_id,
            "source": self.source,
            "signal_type": self.signal_type.value,
            "message": self.message,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata.copy(),
        }