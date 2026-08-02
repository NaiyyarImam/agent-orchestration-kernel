"""Ports consumed by the executive orchestration layer."""

from __future__ import annotations

from typing import Any, Protocol

from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask
from kernel.intelligence.context import Context


class ConfigProvider(Protocol):
    """Configuration source retained by the executive for inspection."""


class MemoryService(Protocol):
    async def health_check(self) -> bool: ...

    async def close(self) -> None: ...


class ModelService(Protocol):
    async def health_check(self) -> dict[str, bool]: ...


class ToolService(Protocol):
    async def health_check(self) -> bool: ...


class CapabilityService(Protocol):
    """Port to the capability adapter manager.

    can_handle uses the same intent-resolution strategy the manager uses
    for dispatch (adapter.supports(intent)): an intent is dispatchable
    only when some registered adapter supports it.
    """

    def can_handle(self, intent: str) -> bool: ...

    async def execute(self, task: CapabilityTask) -> CapabilityResult: ...

    async def health_check(self) -> bool: ...

    async def initialize_all(self) -> None: ...

    async def shutdown_all(self) -> None: ...


class PolicyService(Protocol):
    def evaluate(self, intent: str) -> Any: ...


class RecoveryService(Protocol):
    async def async_execute_with_recovery(
        self, operation: Any, *args: Any, **kwargs: Any
    ) -> Any: ...


class ObservabilityService(Protocol):
    def record_request_started(self, objective: str) -> None: ...

    def record_request_completed(self, objective: str) -> None: ...

    def record_request_failed(self, objective: str) -> None: ...


class EnvironmentService(Protocol):
    def get_snapshot(self) -> Any: ...


class PluginService(Protocol):
    """Marker port for optional plugin services."""


class ContextEngine(Protocol):
    """Builds execution context from user input and session state."""

    def build(
        self,
        user_input: str,
        conversation_id: str | None = None,
        session_id: str | None = None,
        timestamp: Any | None = None,
        working_memory: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any: ...

    async def health_check(self) -> dict[str, bool]: ...


class IntentEngine(Protocol):
    """Classifies user input into structured intent."""

    def classify(self, text: str) -> Any: ...

    async def health_check(self) -> bool: ...


class ReasoningEngine(Protocol):
    """Maps intent to capability with priority and confirmation requirements."""

    def reason(self, intent: Any) -> Any: ...

    async def health_check(self) -> bool: ...


class DecisionEngine(Protocol):
    """Produces executable decision from intent and reasoning."""

    def decide(self, intent: Any, reasoning: Any) -> Any: ...

    async def health_check(self) -> bool: ...


class PlanningEngine(Protocol):
    """Converts decision into concrete execution plan."""

    def create_plan(self, decision: Any) -> Any: ...

    def validate(self, plan: Any) -> bool: ...

    async def health_check(self) -> dict[str, bool]: ...


class ExecutionEngine(Protocol):
    """Executes plans through the capability boundary."""

    async def execute(self, plan: Any, context: Context | None = None) -> Any: ...

    async def health_check(self) -> dict[str, bool]: ...
