"""In-memory implementation of the Kernel EventBus."""

from __future__ import annotations

from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.events.event_handler import EventHandler
from kernel.events.event_subscription import EventSubscription


class InMemoryEventBus(EventBus):
    """Concrete in-memory EventBus implementation.

    This class currently reuses the synchronous EventBus implementation.
    It exists as the replaceable infrastructure layer for future backends
    such as Redis, NATS, Kafka, or other distributed transports.
    """

    def subscribe(self, handler: EventHandler) -> EventSubscription:
        return super().subscribe(handler)

    def unsubscribe(self, handler: EventHandler) -> bool:
        return super().unsubscribe(handler)

    def publish(self, event: Event) -> None:
        super().publish(event)

    async def health_check(self) -> bool:
        """Return True while the in-memory backend is operational."""
        return True