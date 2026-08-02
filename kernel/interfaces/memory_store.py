

"""Abstract interface for JARVIS memory storage backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """Backend-agnostic contract for long-term memory storage.

    Concrete implementations (SQLite, Qdrant, ChromaDB, etc.) must implement
    this interface. The Kernel depends only on this contract.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the value associated with a key, or None if absent."""

    @abstractmethod
    async def put(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store or update a value."""

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Compatibility alias for storing or updating a value."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Return True if it existed."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if the key exists."""

    @abstractmethod
    async def query(
        self,
        query: str,
        *,
        memory_type: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memories matching a query."""

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[Any]:
        """Search memories for the high-level memory API."""

    @abstractmethod
    async def keys(self) -> list[str]:
        """Return all stored memory keys."""

    @abstractmethod
    async def clear(self) -> None:
        """Remove all stored memories."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the backend is operational."""

    @abstractmethod
    async def close(self) -> None:
        """Release backend resources."""
