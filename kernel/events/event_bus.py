

from __future__ import annotations

from collections import defaultdict

from kernel.events.event import Event
from kernel.events.event_handler import EventHandler
from kernel.events.event_subscription import EventSubscription


class EventBus:
    """In-memory event bus for publishing and dispatching Kernel events."""

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[EventSubscription]] = defaultdict(list)

    def subscribe(self, handler: EventHandler) -> EventSubscription:
        """Register an event handler and return its subscription."""
        subscription = EventSubscription(handler.event_name, handler)
        self._subscriptions[subscription.event_name].append(subscription)
        return subscription

    def unsubscribe(self, handler: EventHandler) -> bool:
        """Remove an event handler. Returns True if removed."""
        event_name = handler.event_name
        subscriptions = self._subscriptions.get(event_name)
        if not subscriptions:
            return False

        for subscription in list(subscriptions):
            if subscription.handler is handler:
                subscriptions.remove(subscription)
                if not subscriptions:
                    self._subscriptions.pop(event_name, None)
                return True

        return False

    def publish(self, event: Event) -> None:
        """Dispatch an event to all subscribed handlers."""
        for subscription in tuple(self._subscriptions.get(event.name, [])):
            subscription.handler.handle(event)

    def subscriptions_for(self, event_name: str) -> tuple[EventSubscription, ...]:
        """Return subscriptions for the given event name."""
        return tuple(self._subscriptions.get(event_name.strip(), []))

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscriptions.clear()