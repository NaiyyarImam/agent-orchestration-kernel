"""Unit tests for InMemoryCapabilityRegistry."""

from __future__ import annotations

import asyncio

import pytest

from kernel.adapters.capability_registry import InMemoryCapabilityRegistry
from kernel.interfaces.capability_registry import CapabilityMetadata


def test_register_capability_metadata() -> None:
    registry = InMemoryCapabilityRegistry()
    capability = CapabilityMetadata(
        name="coding",
        capability_type="adapter",
        description="Coding capability",
        tags=["code", "python"],
    )

    asyncio.run(registry.register(capability))

    result = asyncio.run(registry.get("coding"))
    assert result.name == "coding"


def test_unregister_unknown_capability_returns_false() -> None:
    registry = InMemoryCapabilityRegistry()

    assert asyncio.run(registry.unregister("missing")) is False


def test_exists_and_search() -> None:
    registry = InMemoryCapabilityRegistry()
    capability = CapabilityMetadata(
        name="research",
        capability_type="adapter",
        description="Research capability",
        tags=["search", "web"],
    )

    asyncio.run(registry.register(capability))

    assert asyncio.run(registry.exists("research")) is True
    matches = asyncio.run(registry.search("web"))
    assert len(matches) == 1
    assert matches[0].name == "research"


def test_health_check() -> None:
    registry = InMemoryCapabilityRegistry()

    assert asyncio.run(registry.health_check()) is True