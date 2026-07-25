

from __future__ import annotations

from .plugin import Plugin


class PluginRegistry:
    """Registry for Kernel plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin by its metadata name."""
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered.")
        self._plugins[name] = plugin

    def unregister(self, name: str) -> None:
        """Remove a plugin if it exists."""
        self._plugins.pop(name, None)

    def get(self, name: str) -> Plugin | None:
        """Return a registered plugin by name, or None."""
        return self._plugins.get(name)

    def list_plugins(self) -> tuple[Plugin, ...]:
        """Return all registered plugins."""
        return tuple(self._plugins.values())

    def has_plugin(self, name: str) -> bool:
        """Return True if a plugin with the given name is registered."""
        return name in self._plugins

    def clear(self) -> None:
        """Remove all registered plugins."""
        self._plugins.clear()

    def __contains__(self, name: object) -> bool:
        """Support the 'in' operator using plugin names."""
        return isinstance(name, str) and name in self._plugins

    def __len__(self) -> int:
        """Return the number of registered plugins."""
        return len(self._plugins)