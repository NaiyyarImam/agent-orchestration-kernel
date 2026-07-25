

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event published within the Kernel."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "kernel"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Event name must not be empty.")

        object.__setattr__(self, "name", self.name.strip())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        return {
            "event_id": self.event_id,
            "name": self.name,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Create an Event from a serialized dictionary."""
        return cls(
            name=data["name"],
            payload=dict(data.get("payload", {})),
            source=data.get("source", "kernel"),
            event_id=data.get("event_id", str(uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(UTC),
        )