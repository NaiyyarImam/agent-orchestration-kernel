from __future__ import annotations

from .plugin import Plugin
from .plugin_registry import PluginRegistry


class PluginManager:
    """Coordinates plugin registration and lifecycle management."""

    def __init__(self) -> None:
        self._registry = PluginRegistry()

    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        self._registry.register(plugin)

    def unregister(self, name: str) -> None:
        """Unregister a plugin by name."""
        self._registry.unregister(name)

    def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        for plugin in self._registry.list_plugins():
            plugin.initialize()

    def shutdown_all(self) -> None:
        """Shut down all registered plugins."""
        for plugin in self._registry.list_plugins():
            plugin.shutdown()

    def get(self, name: str) -> Plugin | None:
        """Return a registered plugin by name, or None."""
        return self._registry.get(name)

    def list_plugins(self) -> tuple[Plugin, ...]:
        """Return all registered plugins."""
        return self._registry.list_plugins()

    def clear(self) -> None:
        """Remove all registered plugins."""
        self._registry.clear()