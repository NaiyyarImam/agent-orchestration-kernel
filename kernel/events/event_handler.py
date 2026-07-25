

from __future__ import annotations

from abc import ABC, abstractmethod

from kernel.events.event import Event


class EventHandler(ABC):
    """Abstract base class for Kernel event handlers."""

    @property
    @abstractmethod
    def event_name(self) -> str:
        """Return the event name this handler subscribes to."""
        raise NotImplementedError

    @abstractmethod
    def handle(self, event: Event) -> None:
        """Process an incoming event."""
        raise NotImplementedError