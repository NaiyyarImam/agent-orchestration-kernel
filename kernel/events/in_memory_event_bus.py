"""In-memory implementation of the canonical Kernel EventBus port."""

from __future__ import annotations

from collections import defaultdict
from inspect import isawaitable
from typing import Any

from kernel.interfaces.event_bus import EventBus, EventHandler


class InMemoryEventBus(EventBus):
    """Concrete in-memory EventBus implementation.

    Handlers may be synchronous or asynchronous. The implementation is
    deliberately transport-independent so a remote bus can replace it.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._subscribers.get(event_type)
        if handlers is None:
            return
        try:
            handlers.remove(handler)
        except ValueError:
            return
        if not handlers:
            self._subscribers.pop(event_type, None)

    async def subscribers(self, event_type: str) -> list[EventHandler]:
        return list(self._subscribers.get(event_type, ()))

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        for handler in tuple(self._subscribers.get(event_type, ())):
            result = handler(dict(payload))
            if isawaitable(result):
                await result

    async def health_check(self) -> bool:
        """Return True while the in-memory backend is operational."""
        return True
