

from __future__ import annotations

import pytest

from kernel.plugin.plugin import Plugin
from kernel.plugin.plugin_metadata import PluginMetadata
from kernel.plugin.plugin_registry import PluginRegistry


class DummyPlugin(Plugin):
    def __init__(self, name: str = "Dummy") -> None:
        self._metadata = PluginMetadata(
            name=name,
            version="1.0.0",
            capabilities=("research",),
        )

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def capabilities(self) -> tuple[str, ...]:
        return self.metadata.capabilities


def test_register_plugin() -> None:
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    assert registry.get("Dummy") is plugin


def test_duplicate_registration_raises() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())
    with pytest.raises(ValueError):
        registry.register(DummyPlugin())


def test_get_missing_plugin_returns_none() -> None:
    registry = PluginRegistry()
    assert registry.get("Missing") is None


def test_unregister_plugin() -> None:
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    registry.unregister("Dummy")
    assert registry.get("Dummy") is None


def test_unregister_missing_plugin_does_not_raise() -> None:
    registry = PluginRegistry()
    registry.unregister("Missing")


def test_list_plugins_returns_tuple() -> None:
    registry = PluginRegistry()
    p1 = DummyPlugin("One")
    p2 = DummyPlugin("Two")
    registry.register(p1)
    registry.register(p2)
    assert registry.list_plugins() == (p1, p2)


def test_has_plugin() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())
    assert registry.has_plugin("Dummy") is True
    assert registry.has_plugin("Missing") is False


def test_clear_registry() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())
    registry.clear()
    assert len(registry) == 0


def test_contains_operator() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())
    assert "Dummy" in registry
    assert "Missing" not in registry


def test_len_operator() -> None:
    registry = PluginRegistry()
    assert len(registry) == 0
    registry.register(DummyPlugin())
    assert len(registry) == 1