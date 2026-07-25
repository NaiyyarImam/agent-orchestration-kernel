

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Immutable metadata describing a Kernel plugin."""

    name: str
    version: str
    author: str | None = None
    description: str | None = None
    capabilities: tuple[str, ...] = ()
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Plugin name cannot be empty.")

        if not self.version.strip():
            raise ValueError("Plugin version cannot be empty.")

        normalized = tuple(
            capability.strip().lower()
            for capability in self.capabilities
            if capability.strip()
        )

        object.__setattr__(self, "capabilities", normalized)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the metadata to a dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginMetadata":
        """Create PluginMetadata from a dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            author=data.get("author"),
            description=data.get("description"),
            capabilities=tuple(data.get("capabilities", ())),
            enabled=data.get("enabled", True),
        )