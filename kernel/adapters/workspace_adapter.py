

"""Workspace capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.interfaces.storage import Storage


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
        return intent.lower() in {
            "workspace",
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "delete_file",
            "move_file",
        }

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("WorkspaceAdapter has not been initialized.")

        if task.intent.lower() == "read_file":
            return await self._execute_read_file(task)

        messages = {
            "workspace": "Workspace placeholder executed successfully.",
            "write_file": "Write file placeholder.",
            "list_directory": "List directory placeholder.",
            "create_directory": "Create directory placeholder.",
            "delete_file": "Delete file placeholder.",
            "move_file": "Move file placeholder.",
        }

        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "payload": task.payload,
                "context": task.context,
                "message": messages.get(
                    task.intent,
                    "Workspace placeholder executed successfully.",
                ),
            },
            metadata={
                "adapter": self.name,
                "status": "placeholder",
            },
            execution_time_ms=0.0,
        )

    async def _execute_read_file(self, task: CapabilityTask) -> CapabilityResult:
        path = task.payload.get("path")
        if not path:
            return CapabilityResult(
                success=False,
                error="Missing 'path' in payload",
                metadata={
                    "adapter": self.name,
                    "status": "error",
                },
                execution_time_ms=0.0,
            )

        # If StorageManager not injected, fall back to placeholder behavior
        if self._storage is None:
            return CapabilityResult(
                success=True,
                data={
                    "intent": task.intent,
                    "payload": task.payload,
                    "context": task.context,
                    "message": "Read file placeholder.",
                },
                metadata={
                    "adapter": self.name,
                    "status": "placeholder",
                },
                execution_time_ms=0.0,
            )

        try:
            full_path = self._storage.path(path)
            content = full_path.read_text(encoding="utf-8")
            return CapabilityResult(
                success=True,
                data={
                    "intent": task.intent,
                    "payload": task.payload,
                    "context": task.context,
                    "content": content,
                },
                metadata={
                    "adapter": self.name,
                    "status": "ok",
                },
                execution_time_ms=0.0,
            )
        except FileNotFoundError:
            return CapabilityResult(
                success=False,
                error=f"File not found: {path}",
                metadata={
                    "adapter": self.name,
                    "status": "error",
                },
                execution_time_ms=0.0,
            )
        except Exception as e:
            return CapabilityResult(
                success=False,
                error=f"Failed to read file: {e}",
                metadata={
                    "adapter": self.name,
                    "status": "error",
                },
                execution_time_ms=0.0,
            )

    async def shutdown(self) -> None:
        self._initialized = False
