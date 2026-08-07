
from __future__ import annotations

import pytest

from kernel.plugin.plugin import Plugin
from kernel.plugin.plugin_metadata import PluginMetadata


class DummyPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Dummy",
            version="1.0.0",
            capabilities=("research",),
        )

    def initialize(self) -> None:
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False

    def capabilities(self) -> tuple[str, ...]:
        return self.metadata.capabilities


def test_plugin_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Plugin()


def test_plugin_metadata_property() -> None:
    plugin = DummyPlugin()
    assert isinstance(plugin.metadata, PluginMetadata)
    assert plugin.metadata.name == "Dummy"


def test_plugin_initialize() -> None:
    plugin = DummyPlugin()
    plugin.initialize()
    assert plugin.initialized is True


def test_plugin_shutdown() -> None:
    plugin = DummyPlugin()
    plugin.initialize()
    plugin.shutdown()
    assert plugin.initialized is False


def test_plugin_capabilities() -> None:
    plugin = DummyPlugin()
    assert plugin.capabilities() == ("research",)
