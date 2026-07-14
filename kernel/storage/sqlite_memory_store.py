"""
SQLite-backed implementation of the MemoryStore interface.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from kernel.interfaces.memory_store import MemoryStore


class SQLiteMemoryStore(MemoryStore):
    """SQLite implementation of the MemoryStore interface."""

    def __init__(self, database: str | Path) -> None:
        self._db_path = Path(database)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(self._db_path)
        self._connection.row_factory = sqlite3.Row

        self._initialize()

    def _initialize(self) -> None:
        cursor = self._connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self._connection.commit()

    async def put(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        cursor = self._connection.cursor()

        cursor.execute(
            """
            INSERT INTO memories(key, value, memory_type, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET
                value=excluded.value,
                memory_type=excluded.memory_type,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                key,
                json.dumps(value),
                memory_type,
                json.dumps(metadata or {}),
            ),
        )

        self._connection.commit()

    async def set(
        self,
        key: str,
        value: Any,
        *,
        memory_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Compatibility alias for put()."""
        await self.put(
            key,
            value,
            memory_type=memory_type,
            metadata=metadata,
        )

    async def get(self, key: str) -> Any:
        cursor = self._connection.cursor()

        cursor.execute(
            "SELECT value FROM memories WHERE key=?",
            (key,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return json.loads(row["value"])

    async def delete(self, key: str) -> bool:
        cursor = self._connection.cursor()

        cursor.execute(
            "DELETE FROM memories WHERE key=?",
            (key,),
        )

        self._connection.commit()

        return cursor.rowcount > 0

    async def exists(self, key: str) -> bool:
        cursor = self._connection.cursor()

        cursor.execute(
            "SELECT 1 FROM memories WHERE key=?",
            (key,),
        )

        return cursor.fetchone() is not None

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[Any]:
        cursor = self._connection.cursor()

        cursor.execute(
            """
            SELECT value
            FROM memories
            WHERE key LIKE ? OR value LIKE ?
            LIMIT ?
            """,
            (
                f"%{query}%",
                f"%{query}%",
                limit,
            ),
        )

        return [
            json.loads(row["value"])
            for row in cursor.fetchall()
        ]

    async def query(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[Any]:
        return await self.search(query, limit=limit)

    async def keys(self) -> list[str]:
        cursor = self._connection.cursor()

        cursor.execute(
            "SELECT key FROM memories ORDER BY key"
        )

        return [
            row["key"]
            for row in cursor.fetchall()
        ]

    async def clear(self) -> None:
        cursor = self._connection.cursor()

        cursor.execute(
            "DELETE FROM memories"
        )

        self._connection.commit()

    async def health_check(self) -> bool:
        try:
            self._connection.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    async def close(self) -> None:
        self._connection.close()