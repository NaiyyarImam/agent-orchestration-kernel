

"""Abstract interface for the JARVIS Kernel event bus."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


EventHandler = Callable[[dict[str, Any]], Any]


class EventBus(ABC):
    """Framework-independent publish/subscribe contract.

    The Kernel communicates internally through this interface rather than
    allowing components to call each other directly.
    """

    @abstractmethod
    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish an event to all interested subscribers."""

    @abstractmethod
    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register a handler for an event type."""

    @abstractmethod
    async def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Remove a previously registered handler."""

    @abstractmethod
    async def subscribers(
        self,
        event_type: str,
    ) -> list[EventHandler]:
        """Return the handlers registered for an event type."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the event bus is operational."""