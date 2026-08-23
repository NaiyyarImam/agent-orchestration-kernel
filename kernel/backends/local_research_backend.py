"""Local keyword research backend using the existing MemoryStore.

This backend provides local-only research capability by searching the
kernel's memory store. It performs ZERO network calls and uses only
existing infrastructure.
"""

from __future__ import annotations

from typing import Any, Iterable

from kernel.interfaces.research_backend import ResearchResult
from kernel.interfaces.memory_store import MemoryStore


class LocalResearchBackend:
    """Local research backend backed by MemoryStore.

    Delegates search to the existing MemoryStore implementation and
    converts stored memory entries into ResearchResult objects.
    """

    def __init__(self, memory_store: MemoryStore) -> None:
        self._store = memory_store

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        context: dict[str, Any] | None = None,
    ) -> Iterable[ResearchResult] | None:
        """Search local memory for findings matching query.

        Uses the MemoryStore's existing search implementation (LIKE-based
        substring matching over stored JSON values) and converts results
        to ResearchResult format.
        """
        raw_results = await self._store.search(query, limit=limit)

        results: list[ResearchResult] = []
        for item in raw_results:
            if isinstance(item, dict):
                title = item.get("title", "Memory entry")
                snippet = item.get("snippet", str(item))
                url = item.get("url")
            else:
                title = "Memory entry"
                snippet = str(item)
                url = None

            results.append(
                ResearchResult(
                    title=title,
                    snippet=snippet,
                    url=url,
                    source="local",
                )
            )

        return results

    async def initialize(self) -> None:
        """Initialize backend resources (no-op; store is already initialized)."""
        pass

    async def shutdown(self) -> None:
        """Release backend resources (no-op; store lifecycle managed elsewhere)."""
        pass

    async def health_check(self) -> bool:
        """Return backend health status by delegating to the store."""
        return await self._store.health_check()

    name = "local"
    description = "Keyword search over local JARVIS memories"
    capabilities = ("keyword_search",)