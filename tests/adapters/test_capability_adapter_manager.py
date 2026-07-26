"""Unit tests for CapabilityAdapterManager."""

from __future__ import annotations

import pytest


from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager


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