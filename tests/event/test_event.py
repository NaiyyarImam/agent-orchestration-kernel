

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.events.event import Event


def test_event_defaults() -> None:
    event = Event(name="kernel.started")

    assert event.name == "kernel.started"
    assert event.source == "kernel"
    assert event.payload == {}
    assert event.event_id
    assert event.timestamp is not None


def test_empty_event_name_raises() -> None:
    with pytest.raises(ValueError):
        Event(name="")

    with pytest.raises(ValueError):
        Event(name="   ")


def test_event_name_is_trimmed() -> None:
    event = Event(name="  kernel.started  ")
    assert event.name == "kernel.started"


def test_event_id_is_generated() -> None:
    event = Event(name="test")
    assert isinstance(event.event_id, str)
    assert len(event.event_id) > 0


def test_timestamp_is_generated() -> None:
    event = Event(name="test")
    assert event.timestamp is not None


def test_to_dict() -> None:
    event = Event(
        name="kernel.started",
        source="bootstrap",
        payload={"version": "1.5.0"},
    )

    data = event.to_dict()

    assert data["name"] == "kernel.started"
    assert data["source"] == "bootstrap"
    assert data["payload"] == {"version": "1.5.0"}
    assert "event_id" in data
    assert "timestamp" in data


def test_from_dict() -> None:
    original = Event(
        name="kernel.started",
        source="bootstrap",
        payload={"version": "1.5.0"},
    )

    recreated = Event.from_dict(original.to_dict())

    assert recreated.name == original.name
    assert recreated.source == original.source
    assert recreated.payload == original.payload
    assert recreated.event_id == original.event_id
    assert recreated.timestamp == original.timestamp


def test_event_is_frozen() -> None:
    event = Event(name="test")

    with pytest.raises(FrozenInstanceError):
        event.name = "changed"