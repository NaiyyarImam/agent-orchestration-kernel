from __future__ import annotations

import pytest

from kernel.events.event_bus import EventBus as LegacyEventBus
from kernel.events.in_memory_event_bus import InMemoryEventBus
from kernel.interfaces.event_bus import EventBus


@pytest.mark.asyncio
async def test_in_memory_bus_implements_canonical_port() -> None:
    bus: EventBus = InMemoryEventBus()

    assert await bus.subscribers("kernel.started") == []


def test_legacy_event_bus_import_remains_available() -> None:
    assert isinstance(LegacyEventBus(), InMemoryEventBus)


@pytest.mark.asyncio
async def test_publish_delivers_payload_to_sync_handler() -> None:
    bus = InMemoryEventBus()
    received: list[dict[str, object]] = []

    def handler(payload: dict[str, object]) -> None:
        received.append(payload)

    await bus.subscribe("kernel.started", handler)
    await bus.publish("kernel.started", {"source": "kernel"})

    assert received == [{"source": "kernel"}]


@pytest.mark.asyncio
async def test_publish_delivers_payload_to_async_handler() -> None:
    bus = InMemoryEventBus()
    received: list[dict[str, object]] = []

    async def handler(payload: dict[str, object]) -> None:
        received.append(payload)

    await bus.subscribe("kernel.started", handler)
    await bus.publish("kernel.started", {"version": "2.0"})

    assert received == [{"version": "2.0"}]


@pytest.mark.asyncio
async def test_unsubscribe_removes_handler() -> None:
    bus = InMemoryEventBus()

    def handler(payload: dict[str, object]) -> None:
        pass

    await bus.subscribe("kernel.started", handler)
    await bus.unsubscribe("kernel.started", handler)

    assert await bus.subscribers("kernel.started") == []


@pytest.mark.asyncio
async def test_health_check() -> None:
    assert await InMemoryEventBus().health_check() is True
