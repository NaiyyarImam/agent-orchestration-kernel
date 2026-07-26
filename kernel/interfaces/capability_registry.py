

"""Capability Registry interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilityMetadata:
    """Metadata describing a registered capability."""

    name: str
    capability_type: str
    description: str
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry(ABC):
    """Abstract interface for capability registration and discovery."""

    @abstractmethod
    async def register(self, capability: CapabilityMetadata) -> None:
        """Register a capability."""

    @abstractmethod
    async def unregister(self, name: str) -> bool:
        """Unregister a capability."""

    @abstractmethod
    async def get(self, name: str) -> CapabilityMetadata:
        """Return metadata for a registered capability."""

    @abstractmethod
    async def list_capabilities(self) -> list[CapabilityMetadata]:
        """Return all registered capabilities."""

    @abstractmethod
    async def exists(self, name: str) -> bool:
        """Return whether a capability is registered."""

    @abstractmethod
    async def search(self, tag: str) -> list[CapabilityMetadata]:
        """Return capabilities matching a tag."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return registry health."""