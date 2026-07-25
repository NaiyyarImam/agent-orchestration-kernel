

"""Memory manager for the JARVIS Kernel.

Coordinates all memory operations through the MemoryStore interface.
The Kernel never talks directly to a storage backend.
"""

from __future__ import annotations

from typing import Any

from kernel.interfaces.memory_store import MemoryStore


class MemoryManager:
    """High-level API for Kernel memory operations."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def save(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a memory."""
        await self._store.set(
            key=key,
            value=value,
            memory_type=memory_type,
            metadata=metadata or {},
        )

    async def load(self, key: str) -> Any:
        """Load a memory by key."""
        return await self._store.get(key)

    async def update(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update an existing memory."""
        await self.save(
            key,
            value,
            memory_type=memory_type,
            metadata=metadata,
        )

    async def delete(self, key: str) -> bool:
        """Delete a memory."""
        return await self._store.delete(key)

    async def exists(self, key: str) -> bool:
        """Return True if the memory exists."""
        return await self._store.exists(key)

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[Any]:
        """Search stored memories."""
        return await self._store.search(query=query, limit=limit)

    async def list_memories(self) -> list[str]:
        """Return all memory keys."""
        return await self._store.keys()

    async def memory_count(self) -> int:
        """Return the number of stored memories."""
        return len(await self.list_memories())

    async def health_check(self) -> bool:
        """Return True if the underlying store is healthy."""
        return await self._store.health_check()

    async def memory_info(self) -> dict[str, Any]:
        """Return metadata describing the configured memory manager."""
        keys = await self.list_memories()
        return {
            "store": type(self._store).__name__,
            "memory_count": len(keys),
        }

    @property
    def store(self) -> MemoryStore:
        """Expose the configured MemoryStore implementation."""
        return self._store

    async def has_memory(self, key: str) -> bool:
        """Return whether a memory with the given key exists."""
        return await self.exists(key)