

from __future__ import annotations

from dataclasses import dataclass

from kernel.events.event_handler import EventHandler


@dataclass(frozen=True, slots=True)
class EventSubscription:
    """Represents a subscription between an event name and its handler."""

    event_name: str
    handler: EventHandler

    def __post_init__(self) -> None:
        if not self.event_name or not self.event_name.strip():
            raise ValueError("Event name must not be empty.")

        object.__setattr__(self, "event_name", self.event_name.strip())

    def matches(self, event_name: str) -> bool:
        """Return True if this subscription matches the given event name."""
        return self.event_name == event_name.strip()