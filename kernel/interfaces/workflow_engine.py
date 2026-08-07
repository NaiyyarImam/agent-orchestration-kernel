

"""Abstract interface for the JARVIS Kernel workflow engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorkflowEngine(ABC):
    """Framework-agnostic contract for workflow execution.

    Implementations may use LangGraph, a custom DAG engine, or another
    orchestration backend. The Kernel depends only on this interface.
    """

    @abstractmethod
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
        """Register a workflow together with optional metadata."""

    @abstractmethod
    async def execute(
        self,
        workflow_name: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a registered workflow and return its result."""

    @abstractmethod
    async def cancel(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""

    @abstractmethod
    async def status(self, workflow_id: str) -> dict[str, Any]:
        """Return the current status of a workflow."""

    @abstractmethod
    async def list_workflows(self) -> list[str]:
        """Return the names of all registered workflows."""

    @abstractmethod
    async def workflow_metadata(
        self,
        workflow_name: str,
    ) -> dict[str, Any]:
        """Return metadata for a registered workflow."""

    @abstractmethod
    async def workflow_history(self) -> list[dict[str, Any]]:
        """Return historical workflow execution records."""

    @abstractmethod
    async def completed_workflows(self) -> list[dict[str, Any]]:
        """Return completed, failed, and cancelled workflow records."""

    @abstractmethod
    async def clear_history(self) -> None:
        """Clear stored workflow execution history."""

    @abstractmethod
    async def running_workflows(self) -> list[dict[str, Any]]:
        """Return metadata for currently running workflows."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the workflow engine is operational."""