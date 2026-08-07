

"""Unit tests for SQLiteMemoryStore."""

from __future__ import annotations

import pytest

from kernel.storage.sqlite_memory_store import SQLiteMemoryStore


@pytest.mark.asyncio
async def test_set_and_get(memory_store: SQLiteMemoryStore) -> None:
    await memory_store.set("user", {"name": "Jarvis"})
    value = await memory_store.get("user")
    assert value == {"name": "Jarvis"}


@pytest.mark.asyncio
async def test_exists(memory_store: SQLiteMemoryStore) -> None:
    await memory_store.set("key", "value")
    assert await memory_store.exists("key") is True
    assert await memory_store.exists("missing") is False


@pytest.mark.asyncio
async def test_delete(memory_store: SQLiteMemoryStore) -> None:
    await memory_store.set("temp", "data")
    assert await memory_store.delete("temp") is True
    assert await memory_store.get("temp") is None


@pytest.mark.asyncio
async def test_keys(memory_store: SQLiteMemoryStore) -> None:
    await memory_store.set("alpha", 1)
    await memory_store.set("beta", 2)
    keys = await memory_store.keys()
    assert "alpha" in keys
    assert "beta" in keys


@pytest.mark.asyncio
async def test_search(memory_store: SQLiteMemoryStore) -> None:
    await memory_store.set("jarvis", {"value": "assistant"})
    results = await memory_store.search("jarvis")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_health_check(memory_store: SQLiteMemoryStore) -> None:
    assert await memory_store.health_check() is True