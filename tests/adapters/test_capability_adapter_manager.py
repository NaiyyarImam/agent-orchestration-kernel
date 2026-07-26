

"""Unit tests for CapabilityAdapterManager."""

from __future__ import annotations

import pytest


from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.capability_registry import InMemoryCapabilityRegistry
from kernel.interfaces.capability_registry import CapabilityMetadata


class DummyAdapter:
    """Simple adapter used for registry testing."""

    def __init__(self, name: str) -> None:
        self.name = name


def test_register_adapter() -> None:
    manager = CapabilityAdapterManager()
    adapter = DummyAdapter("coding")

    manager.register(adapter)

    assert manager.get("coding") is adapter


def test_register_multiple_adapters() -> None:
    manager = CapabilityAdapterManager()

    manager.register(DummyAdapter("coding"))
    manager.register(DummyAdapter("research"))

    assert manager.get("coding").name == "coding"
    assert manager.get("research").name == "research"


def test_duplicate_adapter_registration_raises() -> None:
    manager = CapabilityAdapterManager()

    manager.register(DummyAdapter("coding"))

    with pytest.raises((ValueError, KeyError)):
        manager.register(DummyAdapter("coding"))


def test_unknown_adapter_raises_key_error() -> None:
    manager = CapabilityAdapterManager()

    with pytest.raises(KeyError):
        manager.get("does-not-exist")


# Additional tests for InMemoryCapabilityRegistry and CapabilityMetadata
def test_register_capability_metadata() -> None:
    registry = InMemoryCapabilityRegistry()
    capability = CapabilityMetadata(
        name="coding",
        capability_type="adapter",
        description="Coding capability",
        tags=["code", "python"],
    )

    import asyncio
    asyncio.run(registry.register(capability))

    result = asyncio.run(registry.get("coding"))
    assert result.name == "coding"


def test_unregister_unknown_capability_returns_false() -> None:
    registry = InMemoryCapabilityRegistry()

    import asyncio
    assert asyncio.run(registry.unregister("missing")) is False


def test_exists_and_search() -> None:
    registry = InMemoryCapabilityRegistry()
    capability = CapabilityMetadata(
        name="research",
        capability_type="adapter",
        description="Research capability",
        tags=["search", "web"],
    )

    import asyncio
    asyncio.run(registry.register(capability))

    assert asyncio.run(registry.exists("research")) is True
    matches = asyncio.run(registry.search("web"))
    assert len(matches) == 1
    assert matches[0].name == "research"


def test_health_check() -> None:
    registry = InMemoryCapabilityRegistry()

    import asyncio
    assert asyncio.run(registry.health_check()) is True