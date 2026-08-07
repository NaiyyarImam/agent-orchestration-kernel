"""Memory capability adapter for the JARVIS Kernel.

The adapter is a pure translation boundary: it converts a CapabilityTask
into a MemoryManager operation and converts the outcome back into a
CapabilityResult. It owns no memory business logic and never talks to a
MemoryStore backend directly; MemoryManager is the single memory owner.
"""

from __future__ import annotations

import hashlib
from typing import Any

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.memory.memory_manager import MemoryManager

_MEMORY_INTENTS: frozenset[str] = frozenset(
    {"remember", "recall", "search_memory", "forget"}
)

_DEFAULT_MEMORY_TYPE: str = "general"
_DEFAULT_SEARCH_LIMIT: int = 10


class MemoryAdapter(CapabilityAdapter):
    def __init__(self, memory: MemoryManager | None = None) -> None:
        self._memory = memory
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent in _MEMORY_INTENTS

    @property
    def name(self) -> str:
        return "memory"

    @property
    def capability_type(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return "Provides long-term and working memory capabilities."

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("MemoryAdapter is not initialized.")
        if not self.supports(task.intent):
            raise ValueError(f"Intent '{task.intent}' not supported by MemoryAdapter.")

        if self._memory is None:
            return self._failed(
                task, "Memory manager is not configured for the memory adapter."
            )

        try:
            if task.intent == "remember":
                return await self._execute_remember(task)
            if task.intent == "recall":
                return await self._execute_recall(task)
            if task.intent == "search_memory":
                return await self._execute_search_memory(task)
            return await self._execute_forget(task)
        except Exception as exc:
            return self._failed(task, f"Memory operation failed: {exc}")

    async def _execute_remember(self, task: CapabilityTask) -> CapabilityResult:
        value = task.payload.get(
            "value", task.payload.get("text", task.payload.get("user_input"))
        )
        if value is None:
            return self._failed(task, "Missing 'value' in payload")

        key = str(task.payload.get("key") or self._derive_key(value))
        memory_type = str(task.payload.get("memory_type", _DEFAULT_MEMORY_TYPE))
        metadata = task.payload.get("metadata") or {}

        await self._memory.save(
            key,
            value,
            memory_type=memory_type,
            metadata=metadata,
        )

        return self._ok(
            task,
            data={"key": key, "status": "stored"},
        )

    async def _execute_recall(self, task: CapabilityTask) -> CapabilityResult:
        key = task.payload.get("key")
        if not key:
            return self._failed(task, "Missing 'key' in payload")

        value = await self._memory.load(str(key))
        if value is None:
            return self._failed(task, f"Memory not found: {key}")

        return self._ok(
            task,
            data={"key": key, "value": value},
        )

    async def _execute_search_memory(self, task: CapabilityTask) -> CapabilityResult:
        query = task.payload.get(
            "query", task.payload.get("text", task.payload.get("user_input"))
        )
        if not query:
            return self._failed(task, "Missing 'query' in payload")

        limit = _DEFAULT_SEARCH_LIMIT
        raw_limit = task.payload.get("limit")
        if raw_limit is not None:
            limit = int(raw_limit)

        results = await self._memory.search(str(query), limit=limit)

        return self._ok(
            task,
            data={"query": query, "results": results},
        )

    async def _execute_forget(self, task: CapabilityTask) -> CapabilityResult:
        key = task.payload.get("key")
        if not key:
            return self._failed(task, "Missing 'key' in payload")

        deleted = await self._memory.delete(str(key))
        if not deleted:
            return self._failed(task, f"Memory not found: {key}")

        return self._ok(
            task,
            data={"key": key, "status": "forgotten"},
        )

    @staticmethod
    def _derive_key(value: Any) -> str:
        """Derive a deterministic key when the caller does not supply one."""
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]

    def _ok(self, task: CapabilityTask, *, data: dict[str, Any]) -> CapabilityResult:
        return CapabilityResult(
            success=True,
            data={"intent": task.intent, "payload": task.payload, **data},
            metadata={
                "adapter": self.name,
                "status": "ok",
            },
            execution_time_ms=0.0,
        )

    def _failed(self, task: CapabilityTask, error: str) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            error=error,
            metadata={
                "adapter": self.name,
                "status": "error",
            },
            execution_time_ms=0.0,
        )
