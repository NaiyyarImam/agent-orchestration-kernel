

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
    ) -> None:
        """Register a workflow with the engine."""

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
    async def health_check(self) -> bool:
        """Return True if the workflow engine is operational."""