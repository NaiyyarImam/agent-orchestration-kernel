"""Workflow manager for the JARVIS Kernel.

Framework-independent implementation of the WorkflowEngine interface.

This manager provides a lightweight in-memory workflow engine. It can
later be backed by LangGraph or another orchestration framework without
changing the Executive Engine.
"""

from __future__ import annotations

import uuid
from typing import Any

from datetime import UTC, datetime

from kernel.interfaces.workflow_engine import WorkflowEngine


class WorkflowManager(WorkflowEngine):
    """Simple in-memory workflow manager."""

    def __init__(self) -> None:
        self._workflows: dict[str, Any] = {}
        self._workflow_metadata: dict[str, dict[str, Any]] = {}
        self._running: dict[str, dict[str, Any]] = {}
        self._history: dict[str, dict[str, Any]] = {}

    async def register_workflow(
        self,
        name: str,
        workflow: Any,
        *,
        description: str | None = None,
        version: str = "1.0.0",
        tags: list[str] | None = None,
        author: str | None = None,
    ) -> None:
        """Register a workflow."""
        self._workflows[name] = workflow
        self._workflow_metadata[name] = {
            "name": name,
            "description": description,
            "version": version,
            "tags": list(tags or []),
            "author": author,
            "registered_at": datetime.now(UTC),
        }

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
        started_at = datetime.now(UTC)

        workflow_state = {
            "id": workflow_id,
            "name": workflow_name,
            "status": "running",
            "started_at": started_at,
            "completed_at": None,
            "failed_at": None,
            "cancelled_at": None,
        }

        self._running[workflow_id] = workflow_state

        try:
            if callable(workflow):
                result = workflow(context or {})
                if hasattr(result, "__await__"):
                    result = await result
            else:
                result = workflow

            workflow_state["status"] = "completed"
            workflow_state["completed_at"] = datetime.now(UTC)
            self._history[workflow_id] = dict(workflow_state)
            self._running.pop(workflow_id, None)
            return result

        except Exception:
            workflow_state["status"] = "failed"
            workflow_state["failed_at"] = datetime.now(UTC)
            self._history[workflow_id] = dict(workflow_state)
            self._running.pop(workflow_id, None)
            raise

    async def cancel(
        self,
        workflow_id: str,
    ) -> bool:
        """Cancel a running workflow."""

        if workflow_id not in self._running:
            return False

        self._running[workflow_id]["status"] = "cancelled"
        self._running[workflow_id]["cancelled_at"] = datetime.now(UTC)
        self._history[workflow_id] = dict(self._running[workflow_id])
        self._running.pop(workflow_id, None)
        return True

    async def status(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Return workflow status."""
        if workflow_id in self._running:
            return self._running[workflow_id]
        if workflow_id in self._history:
            return self._history[workflow_id]
        return {"status": "unknown"}

    async def is_running(self, workflow_id: str) -> bool:
        """Return whether the specified workflow is currently running."""
        workflow = await self.status(workflow_id)
        return workflow.get("status") == "running"

    async def list_workflows(self) -> list[str]:
        """Return registered workflows."""

        return sorted(self._workflows.keys())

    async def workflow_metadata(
        self,
        workflow_name: str,
    ) -> dict[str, Any]:
        """Return metadata for a registered workflow."""
        if workflow_name not in self._workflow_metadata:
            raise KeyError(
                f"Workflow '{workflow_name}' is not registered."
            )
        return dict(self._workflow_metadata[workflow_name])

    async def workflow_count(self) -> int:
        """Return the number of registered workflows."""
        return len(await self.list_workflows())

    async def workflow_history(self) -> list[dict[str, Any]]:
        """Return workflow execution history."""
        return list(self._history.values())

    async def completed_workflows(self) -> list[dict[str, Any]]:
        """Return completed, failed, and cancelled workflows."""
        return [
            workflow
            for workflow in self._history.values()
            if workflow["status"] in {"completed", "failed", "cancelled"}
        ]

    async def clear_history(self) -> None:
        """Clear workflow execution history."""
        self._history.clear()

    async def running_workflows(self) -> list[dict[str, Any]]:
        """Return currently running workflows."""
        return list(self._running.values())

    async def health_check(self) -> bool:
        """Return True if the workflow manager is operational."""
        return True

    async def workflow_info(self) -> dict[str, Any]:
        """Return metadata describing the workflow manager."""
        return {
            "registered_workflows": await self.workflow_count(),
            "running_workflows": len(self._running),
            "completed_workflows": len(self._history),
        }

    async def running_workflow_count(self) -> int:
        """Return the number of workflows currently tracked."""
        return len(self._running)

    async def manager_info(self) -> dict[str, Any]:
        """Return overall workflow manager information."""
        return {
            "healthy": await self.health_check(),
            "registered_workflows": await self.workflow_count(),
            "running_workflows": await self.running_workflow_count(),
        }