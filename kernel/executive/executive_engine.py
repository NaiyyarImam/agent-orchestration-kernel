"""Executive Intelligence Engine for the JARVIS Kernel.

The ExecutiveEngine is the central orchestrator of the Kernel. It coordinates
configuration, memory, models, tools, workflows, events, security, and
capability adapters without depending on any external framework.
"""

from __future__ import annotations
import uuid

from typing import Any

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.config.config_manager import ConfigManager
from kernel.events.in_memory_event_bus import InMemoryEventBus
from kernel.interfaces.capability_adapter import CapabilityTask, CapabilityResult
from kernel.memory.memory_manager import MemoryManager
from kernel.models.model_manager import ModelManager
from kernel.planning.task_plan import TaskPlan
from kernel.security.security_manager import SecurityManager
from kernel.tools.tool_registry import ToolRegistry
from kernel.workflow.workflow_manager import WorkflowManager
from kernel.policy import PolicyEngine


class ExecutiveEngine:
    """Primary orchestration engine for the JARVIS Kernel."""

    def __init__(
        self,
        *,
        config: ConfigManager,
        memory: MemoryManager,
        models: ModelManager,
        tools: ToolRegistry,
        adapters: CapabilityAdapterManager,
        workflows: WorkflowManager,
        events: InMemoryEventBus,
        security: SecurityManager,
        policy: PolicyEngine,
    ) -> None:
        self._config = config
        self._memory = memory
        self._models = models
        self._tools = tools
        self._adapters = adapters
        self._workflows = workflows
        self._events = events
        self._security = security
        self._policy = policy

    async def execute_capability(
        self,
        intent: str,
        payload: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CapabilityResult:
        """Authorize and execute a capability task through the adapter manager."""

        allowed = await self._security.authorize(
            subject="executive_engine",
            action=intent,
            resource="capability",
        )

        if not allowed:
            raise PermissionError(
                f"Execution denied for intent '{intent}'."
            )

        decision = self._policy.evaluate(intent)

        if not decision.allowed:
            raise PermissionError(decision.reason)

        if decision.requires_approval:
            raise PermissionError(
                f"Capability '{intent}' requires approval before execution."
            )

        task = CapabilityTask(
            task_id=str(uuid.uuid4()),
            intent=intent,
            payload=payload,
            context=context or {},
            metadata=metadata or {},
        )

        await self._events.publish(
            "capability.execution.started",
            {"intent": intent},
        )

        result = await self._adapters.execute(task)

        await self._events.publish(
            "capability.execution.completed",
            {
                "intent": intent,
                "success": result.success,
            },
        )

        return result

    async def execute_plan(
        self,
        plan: TaskPlan,
    ) -> list[CapabilityResult]:
        """Execute each step of a task plan sequentially."""

        results: list[CapabilityResult] = []

        for step in plan.steps:
            result = await self.execute_capability(
                step.intent,
                step.payload,
            )
            results.append(result)

        return results

    async def execute_workflow(
        self,
        workflow: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a registered workflow."""
        return await self._workflows.execute(
            workflow,
            context=context,
        )

    async def health_check(self) -> dict[str, Any]:
        """Return the health of all Kernel managers."""
        return {
            "memory": await self._memory.health_check(),
            "models": await self._models.health_check(),
            "tools": await self._tools.health_check(),
            "adapters": await self._adapters.health_check(),
            "workflows": await self._workflows.health_check(),
            "events": await self._events.health_check(),
            "security": await self._security.health_check(),
        }

    @property
    def config(self) -> ConfigManager:
        return self._config

    @property
    def memory(self) -> MemoryManager:
        return self._memory

    @property
    def models(self) -> ModelManager:
        return self._models

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    @property
    def adapters(self) -> CapabilityAdapterManager:
        return self._adapters

    @property
    def workflows(self) -> WorkflowManager:
        return self._workflows

    @property
    def events(self) -> InMemoryEventBus:
        return self._events

    @property
    def security(self) -> SecurityManager:
        return self._security

    @property
    def policy(self) -> PolicyEngine:
        """Return the Kernel Policy Engine."""
        return self._policy