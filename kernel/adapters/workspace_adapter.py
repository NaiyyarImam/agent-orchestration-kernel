"""Workspace capability adapter for the JARVIS Kernel.

The adapter is a pure translation boundary: it converts a CapabilityTask
into a StorageManager operation and converts the outcome back into a
CapabilityResult. It owns no filesystem logic and never touches the
filesystem directly; StorageManager is the single filesystem owner.
"""

from __future__ import annotations

from typing import Any

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.interfaces.storage import Storage

_WORKSPACE_INTENTS: frozenset[str] = frozenset(
    {
        "workspace",
        "read_file",
        "write_file",
        "list_directory",
        "create_directory",
        "delete_file",
        "move_file",
    }
)


class WorkspaceAdapter(CapabilityAdapter):
    """Framework-independent workspace adapter."""

    def __init__(self, storage: Storage | None = None) -> None:
        self._storage = storage
        self._initialized = False

    @property
    def name(self) -> str:
        return "workspace"

    @property
    def capability_type(self) -> str:
        return "workspace"

    @property
    def description(self) -> str:
        return "Provides local workspace and filesystem capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent.lower() in _WORKSPACE_INTENTS

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("WorkspaceAdapter has not been initialized.")

        intent = task.intent.lower()

        if intent == "read_file":
            return await self._execute_read_file(task)
        if intent == "write_file":
            return await self._execute_write_file(task)
        if intent == "delete_file":
            return await self._execute_delete_file(task)
        if intent == "move_file":
            return await self._execute_move_file(task)
        if intent == "create_directory":
            return await self._execute_create_directory(task)
        if intent == "list_directory":
            return await self._execute_list_directory(task)
        if intent == "workspace":
            return self._execute_workspace(task)

        return self._failed(
            task,
            f"Intent '{task.intent}' is not supported by the workspace adapter.",
        )

    async def _execute_read_file(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path")
        if not path:
            return self._failed(task, "Missing 'path' in payload")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            content = storage.read_text(str(path))
        except FileNotFoundError:
            return self._failed(task, f"File not found: {path}")
        except Exception as exc:
            return self._failed(task, f"Failed to read file: {exc}")

        return self._ok(
            task,
            data={"path": path, "content": content},
        )

    async def _execute_write_file(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path")
        content = task.payload.get("content", task.payload.get("text"))
        if not path:
            return self._failed(task, "Missing 'path' in payload")
        if content is None:
            return self._failed(task, "Missing 'content' in payload")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            storage.write_text(str(path), str(content))
        except Exception as exc:
            return self._failed(task, f"Failed to write file: {exc}")

        return self._ok(
            task,
            data={"path": path, "status": "written"},
        )

    async def _execute_delete_file(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path")
        if not path:
            return self._failed(task, "Missing 'path' in payload")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            deleted = storage.delete(str(path))
        except Exception as exc:
            return self._failed(task, f"Failed to delete file: {exc}")

        if not deleted:
            return self._failed(task, f"File not found: {path}")

        return self._ok(
            task,
            data={"path": path, "status": "deleted"},
        )

    async def _execute_move_file(self, task: CapabilityTask) -> CapabilityResult:
        source = task.payload.get("source")
        destination = task.payload.get("destination")
        if not source:
            return self._failed(task, "Missing 'source' in payload")
        if not destination:
            return self._failed(task, "Missing 'destination' in payload")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            storage.move(str(source), str(destination))
        except Exception as exc:
            return self._failed(task, f"Failed to move file: {exc}")

        return self._ok(
            task,
            data={
                "source": source,
                "destination": destination,
                "status": "moved",
            },
        )

    async def _execute_create_directory(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path")
        if not path:
            return self._failed(task, "Missing 'path' in payload")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            storage.ensure_directory(str(path))
        except Exception as exc:
            return self._failed(task, f"Failed to create directory: {exc}")

        return self._ok(
            task,
            data={"path": path, "status": "created"},
        )

    async def _execute_list_directory(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path", "")

        storage = self._storage
        if storage is None:
            return self._failed(
                task, "Storage is not configured for the workspace adapter."
            )

        try:
            entries = storage.list(str(path))
        except Exception as exc:
            return self._failed(task, f"Failed to list directory: {exc}")

        return self._ok(
            task,
            data={
                "path": str(path) if path else ".",
                "entries": [entry.name for entry in entries],
            },
        )

    def _execute_workspace(self, task: CapabilityTask) -> CapabilityResult:
        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "message": "Workspace capability executed successfully.",
                "supported_intents": sorted(_WORKSPACE_INTENTS),
            },
            metadata={
                "adapter": self.name,
                "status": "ok",
            },
            execution_time_ms=0.0,
        )

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

    async def shutdown(self) -> None:
        self._initialized = False
