

from __future__ import annotations

import pytest

from kernel.events.event import Event
from kernel.events.event_handler import EventHandler


class DummyEventHandler(EventHandler):
    def __init__(self) -> None:
        self.handled_event: Event | None = None

    @property
    def event_name(self) -> str:
        return "kernel.started"

    def handle(self, event: Event) -> None:
        self.handled_event = event


def test_event_handler_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        EventHandler()


def test_event_name_property() -> None:
    handler = DummyEventHandler()
    assert handler.event_name == "kernel.started"


def test_handle_receives_event() -> None:
    handler = DummyEventHandler()
    event = Event(name="kernel.started")

    handler.handle(event)

    assert handler.handled_event is event


def test_handle_receives_correct_payload() -> None:
    handler = DummyEventHandler()
    event = Event(
        name="kernel.started",
        payload={"version": "1.5.0"},
    )

    handler.handle(event)

    assert handler.handled_event is not None
    assert handler.handled_event.payload == {"version": "1.5.0"}