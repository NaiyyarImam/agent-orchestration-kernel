

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.plugin.plugin_metadata import PluginMetadata


def test_plugin_metadata_defaults() -> None:
    metadata = PluginMetadata(name="Example", version="1.0.0")

    assert metadata.name == "Example"
    assert metadata.version == "1.0.0"
    assert metadata.author is None
    assert metadata.description is None
    assert metadata.capabilities == ()
    assert metadata.enabled is True


def test_plugin_metadata_empty_name_raises() -> None:
    with pytest.raises(ValueError):
        PluginMetadata(name="", version="1.0.0")


def test_plugin_metadata_empty_version_raises() -> None:
    with pytest.raises(ValueError):
        PluginMetadata(name="Example", version="")


def test_plugin_metadata_normalizes_capabilities() -> None:
    metadata = PluginMetadata(
        name="Example",
        version="1.0.0",
        capabilities=(" Research ", "WORKSPACE", "", " Memory "),
    )

    assert metadata.capabilities == ("research", "workspace", "memory")


def test_plugin_metadata_to_dict() -> None:
    metadata = PluginMetadata(
        name="Example",
        version="1.0.0",
        author="Alice",
        description="Demo plugin",
        capabilities=("research",),
        enabled=False,
    )

    assert metadata.to_dict() == {
        "name": "Example",
        "version": "1.0.0",
        "author": "Alice",
        "description": "Demo plugin",
        "capabilities": ["research"],
        "enabled": False,
    }


def test_plugin_metadata_from_dict() -> None:
    metadata = PluginMetadata.from_dict(
        {
            "name": "Example",
            "version": "1.0.0",
            "author": "Alice",
            "description": "Demo plugin",
            "capabilities": ["research", "workspace"],
            "enabled": False,
        }
    )

    assert metadata.name == "Example"
    assert metadata.version == "1.0.0"
    assert metadata.author == "Alice"
    assert metadata.description == "Demo plugin"
    assert metadata.capabilities == ("research", "workspace")
    assert metadata.enabled is False


def test_plugin_metadata_is_frozen() -> None:
    metadata = PluginMetadata(name="Example", version="1.0.0")

    with pytest.raises(FrozenInstanceError):
        metadata.name = "Other"


def test_plugin_metadata_round_trip() -> None:
    original = PluginMetadata(
        name="Example",
        version="1.0.0",
        author="Alice",
        description="Demo plugin",
        capabilities=("research", "workspace"),
        enabled=False,
    )

    restored = PluginMetadata.from_dict(original.to_dict())

    assert restored == original