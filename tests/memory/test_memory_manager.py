"""Behavioural unit tests for :class:`kernel.memory.memory_manager.MemoryManager`.

``MemoryManager`` currently uses a richer store API than the abstract
``MemoryStore`` contract declares.  The backend below deliberately implements
only the methods the manager actually calls; it is not presented as a
``MemoryStore`` implementation.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from kernel.memory.memory_manager import MemoryManager


class ManagerBackend:
    """In-memory backend exposing the API used by ``MemoryManager``."""

    def __init__(self) -> None:
        self.data: dict[Any, Any] = {}
        self.saved: list[tuple[Any, Any, str, dict[str, Any]]] = []
        self.healthy = True

    async def set(
        self,
        key: Any,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.data[key] = value
        self.saved.append((key, value, memory_type, metadata or {}))

    async def get(self, key: Any) -> Any:
        return self.data.get(key)

    async def delete(self, key: Any) -> bool:
        if key not in self.data:
            return False
        del self.data[key]
        return True

    async def exists(self, key: Any) -> bool:
        return key in self.data

    async def search(self, query: Any, *, limit: int = 10) -> list[Any]:
        return [
            value
            for key, value in self.data.items()
            if str(query) in str(key) or str(query) in str(value)
        ][:limit]

    async def keys(self) -> list[Any]:
        return list(self.data)

    async def health_check(self) -> bool:
        return self.healthy


@pytest.fixture
def backend() -> ManagerBackend:
    return ManagerBackend()


@pytest.fixture
def manager(backend: ManagerBackend) -> MemoryManager:
    return MemoryManager(backend)  # type: ignore[arg-type]


def test_constructor_retains_the_configured_backend(backend: ManagerBackend) -> None:
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert manager.store is backend


@pytest.mark.asyncio
async def test_save_delegates_arguments_and_normalizes_missing_metadata() -> None:
    backend = ManagerBackend()
    backend.set = AsyncMock()
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    await manager.save("profile", {"name": "Ada"}, memory_type="semantic")

    backend.set.assert_awaited_once_with(
        key="profile",
        value={"name": "Ada"},
        memory_type="semantic",
        metadata={},
    )


@pytest.mark.asyncio
async def test_save_forwards_invalid_key_and_value_without_validation() -> None:
    backend = ManagerBackend()
    backend.set = AsyncMock()
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    await manager.save(None, None, metadata={"source": "test"})  # type: ignore[arg-type]

    backend.set.assert_awaited_once_with(
        key=None,
        value=None,
        memory_type="general",
        metadata={"source": "test"},
    )


@pytest.mark.asyncio
async def test_update_reuses_save_for_repeated_writes(manager: MemoryManager, backend: ManagerBackend) -> None:
    await manager.save("status", "new")
    await manager.update("status", "ready", memory_type="working", metadata={"attempt": 2})

    assert await manager.load("status") == "ready"
    assert backend.saved == [
        ("status", "new", "general", {}),
        ("status", "ready", "working", {"attempt": 2}),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [{"nested": [1, 2]}, None])
async def test_load_returns_the_backend_result_unchanged(value: Any) -> None:
    backend = ManagerBackend()
    backend.get = AsyncMock(return_value=value)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.load("missing-or-present") is value
    backend.get.assert_awaited_once_with("missing-or-present")


@pytest.mark.asyncio
async def test_delete_reports_state_transition_and_repeated_delete(manager: MemoryManager) -> None:
    await manager.save("temporary", "value")

    assert await manager.delete("temporary") is True
    assert await manager.exists("temporary") is False
    assert await manager.delete("temporary") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [True, False])
async def test_exists_and_has_memory_return_backend_boolean(result: bool) -> None:
    backend = ManagerBackend()
    backend.exists = AsyncMock(return_value=result)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.exists("key") is result
    assert await manager.has_memory("key") is result
    assert backend.exists.await_args_list == [(("key",), {}), (("key",), {})]


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [10, 0, 2])
async def test_search_forwards_query_and_limit_without_validation(limit: int) -> None:
    expected = ["one", {"two": 2}]
    backend = ManagerBackend()
    backend.search = AsyncMock(return_value=expected)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.search("needle", limit=limit) is expected
    backend.search.assert_awaited_once_with(query="needle", limit=limit)


@pytest.mark.asyncio
async def test_list_memories_returns_backend_keys_unchanged() -> None:
    expected = ["z", "a"]
    backend = ManagerBackend()
    backend.keys = AsyncMock(return_value=expected)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.list_memories() is expected
    backend.keys.assert_awaited_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize("keys", [[], ["one", "two", "three"]])
async def test_memory_count_is_derived_from_current_keys(keys: list[str]) -> None:
    backend = ManagerBackend()
    backend.keys = AsyncMock(return_value=keys)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.memory_count() == len(keys)
    backend.keys.assert_awaited_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize("healthy", [True, False])
async def test_health_check_returns_backend_status(healthy: bool) -> None:
    backend = ManagerBackend()
    backend.health_check = AsyncMock(return_value=healthy)
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.health_check() is healthy
    backend.health_check.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_memory_info_reports_runtime_store_name_and_key_count() -> None:
    class NamedBackend(ManagerBackend):
        pass

    backend = NamedBackend()
    backend.keys = AsyncMock(return_value=["first", "second"])
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    assert await manager.memory_info() == {"store": "NamedBackend", "memory_count": 2}
    backend.keys.assert_awaited_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "backend_method", "arguments"),
    [
        ("save", "set", ("key", "value")),
        ("load", "get", ("key",)),
        ("update", "set", ("key", "value")),
        ("delete", "delete", ("key",)),
        ("exists", "exists", ("key",)),
        ("has_memory", "exists", ("key",)),
        ("search", "search", ("query",)),
        ("list_memories", "keys", ()),
        ("memory_count", "keys", ()),
        ("health_check", "health_check", ()),
        ("memory_info", "keys", ()),
    ],
)
async def test_backend_exceptions_propagate(
    method: str,
    backend_method: str,
    arguments: tuple[Any, ...],
) -> None:
    backend = ManagerBackend()
    failure = RuntimeError(f"{backend_method} failed")
    setattr(backend, backend_method, AsyncMock(side_effect=failure))
    manager = MemoryManager(backend)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match=f"{backend_method} failed"):
        await getattr(manager, method)(*arguments)
