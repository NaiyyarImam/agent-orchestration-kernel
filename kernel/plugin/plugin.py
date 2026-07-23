from __future__ import annotations

from abc import ABC, abstractmethod

from .plugin_metadata import PluginMetadata


class Plugin(ABC):
    """Abstract base class for all JARVIS Kernel plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return immutable metadata describing this plugin."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin and allocate required resources."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources before the plugin is unloaded."""

    @abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        """Return the capabilities exposed by this plugin."""