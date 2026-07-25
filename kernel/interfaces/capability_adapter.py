"""
Capability Adapter Interface

Every external capability (Research, Coding, Browser, Workspace, Voice, etc.)
must implement this interface.

The Kernel never imports framework-specific code directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilityTask:
    """
    Generic request sent from the Executive Intelligence Engine
    to a capability adapter.
    """

    task_id: str
    intent: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CapabilityResult:
    """
    Standard response returned by every adapter.
    """

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class CapabilityAdapter(ABC):
    """
    Base interface implemented by every capability adapter.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter name."""

    @property
    @abstractmethod
    def capability_type(self) -> str:
        """
        Example:
            research
            coding
            browser
            workspace
            voice
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @abstractmethod
    async def initialize(self) -> None:
        """Prepare adapter resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return adapter health."""

    @abstractmethod
    def supports(self, intent: str) -> bool:
        """
        Whether this adapter can execute the requested intent.
        """

    @abstractmethod
    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        """
        Execute a typed task.
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Release resources."""