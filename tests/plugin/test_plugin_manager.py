

from __future__ import annotations

import pytest

from kernel.plugin.plugin import Plugin
from kernel.plugin.plugin_manager import PluginManager
from kernel.plugin.plugin_metadata import PluginMetadata


class DummyPlugin(Plugin):
    def __init__(self, name: str = "Dummy") -> None:
        self._metadata = PluginMetadata(
            name=name,
            version="1.0.0",
            capabilities=("research",),
        )
        self.initialized = False
        self.shutdown_called = False

    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def capabilities(self) -> tuple[str, ...]:
        return self.metadata.capabilities


def test_register_and_get_plugin() -> None:
    manager = PluginManager()
    plugin = DummyPlugin()
    manager.register(plugin)
    assert manager.get("Dummy") is plugin


def test_list_plugins() -> None:
    manager = PluginManager()
    p1 = DummyPlugin("One")
    p2 = DummyPlugin("Two")
    manager.register(p1)
    manager.register(p2)
    assert manager.list_plugins() == (p1, p2)


def test_unregister_plugin() -> None:
    manager = PluginManager()
    manager.register(DummyPlugin())
    manager.unregister("Dummy")
    assert manager.get("Dummy") is None


def test_initialize_all() -> None:
    manager = PluginManager()
    plugin = DummyPlugin()
    manager.register(plugin)
    manager.initialize_all()
    assert plugin.initialized is True


def test_shutdown_all() -> None:
    manager = PluginManager()
    plugin = DummyPlugin()
    manager.register(plugin)
    manager.shutdown_all()
    assert plugin.shutdown_called is True


def test_clear() -> None:
    manager = PluginManager()
    manager.register(DummyPlugin())
    manager.clear()
    assert manager.list_plugins() == ()


def test_duplicate_registration_raises() -> None:
    manager = PluginManager()
    manager.register(DummyPlugin())
    with pytest.raises(ValueError):
        manager.register(DummyPlugin())