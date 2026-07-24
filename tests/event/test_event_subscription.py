

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.events.event import Event
from kernel.events.event_handler import EventHandler
from kernel.events.event_subscription import EventSubscription


class DummyEventHandler(EventHandler):
    @property
    def event_name(self) -> str:
        return "kernel.started"

    def handle(self, event: Event) -> None:
        pass


def test_subscription_defaults() -> None:
    handler = DummyEventHandler()
    subscription = EventSubscription("kernel.started", handler)

    assert subscription.event_name == "kernel.started"
    assert subscription.handler is handler


def test_empty_event_name_raises() -> None:
    handler = DummyEventHandler()

    with pytest.raises(ValueError):
        EventSubscription("", handler)

    with pytest.raises(ValueError):
        EventSubscription("   ", handler)


def test_event_name_is_trimmed() -> None:
    handler = DummyEventHandler()
    subscription = EventSubscription("  kernel.started  ", handler)

    assert subscription.event_name == "kernel.started"


def test_matches_returns_true() -> None:
    handler = DummyEventHandler()
    subscription = EventSubscription("kernel.started", handler)

    assert subscription.matches("kernel.started") is True
    assert subscription.matches("  kernel.started  ") is True


def test_matches_returns_false() -> None:
    handler = DummyEventHandler()
    subscription = EventSubscription("kernel.started", handler)

    assert subscription.matches("kernel.stopped") is False


def test_subscription_is_frozen() -> None:
    handler = DummyEventHandler()
    subscription = EventSubscription("kernel.started", handler)

    with pytest.raises(FrozenInstanceError):
        subscription.event_name = "kernel.stopped"