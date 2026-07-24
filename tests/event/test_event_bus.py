

from __future__ import annotations

from kernel.events.event import Event
from kernel.events.event_bus import EventBus
from kernel.events.event_handler import EventHandler


class DummyHandler(EventHandler):
    def __init__(self, event_name: str = "kernel.started") -> None:
        self._event_name = event_name
        self.events: list[Event] = []

    @property
    def event_name(self) -> str:
        return self._event_name

    def handle(self, event: Event) -> None:
        self.events.append(event)


def test_event_bus_is_empty() -> None:
    bus = EventBus()

    assert bus.subscriptions_for("kernel.started") == ()


def test_subscribe_handler() -> None:
    bus = EventBus()
    handler = DummyHandler()

    subscription = bus.subscribe(handler)

    assert subscription.handler is handler
    assert len(bus.subscriptions_for("kernel.started")) == 1


def test_publish_to_single_handler() -> None:
    bus = EventBus()
    handler = DummyHandler()
    bus.subscribe(handler)

    event = Event(name="kernel.started")
    bus.publish(event)

    assert handler.events == [event]


def test_publish_to_multiple_handlers() -> None:
    bus = EventBus()
    handler1 = DummyHandler()
    handler2 = DummyHandler()

    bus.subscribe(handler1)
    bus.subscribe(handler2)

    event = Event(name="kernel.started")
    bus.publish(event)

    assert handler1.events == [event]
    assert handler2.events == [event]


def test_unsubscribe_handler() -> None:
    bus = EventBus()
    handler = DummyHandler()

    bus.subscribe(handler)

    assert bus.unsubscribe(handler) is True
    assert bus.subscriptions_for("kernel.started") == ()


def test_unsubscribe_missing_handler() -> None:
    bus = EventBus()

    assert bus.unsubscribe(DummyHandler()) is False


def test_clear_subscriptions() -> None:
    bus = EventBus()
    bus.subscribe(DummyHandler())
    bus.subscribe(DummyHandler())

    bus.clear()

    assert bus.subscriptions_for("kernel.started") == ()