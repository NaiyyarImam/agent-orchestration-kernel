"""Shared pytest fixtures for the JARVIS Kernel test suite."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio

from kernel.config.config_manager import ConfigManager
from kernel.storage.sqlite_memory_store import SQLiteMemoryStore


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Provide an isolated storage directory for a test."""
    storage = tmp_path / "storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def temp_database(temp_storage: Path) -> Path:
    """Provide a temporary SQLite database path."""
    return temp_storage / "test_memory.db"


@pytest_asyncio.fixture
async def memory_store(temp_database: Path):
    """Provide a temporary SQLiteMemoryStore instance."""
    store = SQLiteMemoryStore(temp_database)
    try:
        yield store
    finally:
        await store.close()


@pytest.fixture
def config_manager() -> ConfigManager:
    """Provide a ConfigManager instance."""
    return ConfigManager()
