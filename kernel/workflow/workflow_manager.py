"""Workflow manager for the JARVIS Kernel.

Framework-independent implementation of the WorkflowEngine interface.

This manager provides a lightweight in-memory workflow engine. It can
later be backed by LangGraph or another orchestration framework without
changing the Executive Engine.
"""

from __future__ import annotations

import uuid
from typing import Any

from kernel.interfaces.workflow_engine import WorkflowEngine


class WorkflowManager(WorkflowEngine):
    """Simple in-memory workflow manager."""

    def __init__(self) -> None:
        self._workflows: dict[str, Any] = {}
        self._running: dict[str, dict[str, Any]] = {}

    async def register_workflow(
        self,
        name: str,
        workflow: Any,
    ) -> None:
        """Register a workflow."""
        self._workflows[name] = workflow

    async def execute(
        self,
        workflow_name: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a registered workflow."""

        if workflow_name not in self._workflows:
            raise KeyError(
                f"Workflow '{workflow_name}' is not registered."
            )

        workflow = self._workflows[workflow_name]

        workflow_id = str(uuid.uuid4())

        self._running[workflow_id] = {
            "name": workflow_name,
            "status": "running",
        }

        try:
            if callable(workflow):
                result = workflow(context or {})
                if hasattr(result, "__await__"):
                    result = await result
            else:
                result = workflow

            self._running[workflow_id]["status"] = "completed"

            return result

        except Exception:
            self._running[workflow_id]["status"] = "failed"
            raise

    async def cancel(
        self,
        workflow_id: str,
    ) -> bool:
        """Cancel a running workflow."""

        if workflow_id not in self._running:
            return False

        self._running[workflow_id]["status"] = "cancelled"
        return True

    async def status(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Return workflow status."""

        return self._running.get(
            workflow_id,
            {
                "status": "unknown",
            },
        )

    async def is_running(self, workflow_id: str) -> bool:
        """Return whether the specified workflow is currently running."""
        workflow = await self.status(workflow_id)
        return workflow.get("status") == "running"

    async def list_workflows(self) -> list[str]:
        """Return registered workflows."""

        return sorted(self._workflows.keys())

    async def workflow_count(self) -> int:
        """Return the number of registered workflows."""
        return len(await self.list_workflows())

    async def health_check(self) -> bool:
        """Return True if the workflow manager is operational."""
        return True

    async def workflow_info(self) -> dict[str, Any]:
        """Return metadata describing the workflow manager."""
        return {
            "registered_workflows": await self.workflow_count(),
            "running_workflows": len(self._running),
        }