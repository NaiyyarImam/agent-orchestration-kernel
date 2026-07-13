

"""In-memory implementation of the JARVIS Kernel EventBus interface."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable
from typing import Any

from kernel.interfaces.event_bus import EventBus, EventHandler


class InMemoryEventBus(EventBus):
    """Simple asynchronous publish/subscribe event bus.

    This implementation is intended for the initial Kernel and unit tests.
    It can later be replaced by Redis, NATS, Kafka, or another backend
    without changing Kernel code.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Publish an event to all registered subscribers."""
        for handler in self._subscribers[event_type]:
            result = handler(payload)
            if isinstance(result, Awaitable):
                await result

    async def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register an event handler."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    async def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Remove a registered event handler."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def subscribers(
        self,
        event_type: str,
    ) -> list[EventHandler]:
        """Return all subscribers for an event type."""
        return list(self._subscribers[event_type])

    async def health_check(self) -> bool:
        """Return True while the event bus is operational."""
        return True