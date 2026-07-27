

"""Workspace capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.storage.storage_manager import StorageManager


class WorkspaceAdapter(CapabilityAdapter):
    """Framework-independent workspace adapter."""

    def __init__(self, storage: StorageManager | None = None) -> None:
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

        messages = {
            "read_file": "Read file placeholder.",
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

    async def shutdown(self) -> None:
        self._initialized = False