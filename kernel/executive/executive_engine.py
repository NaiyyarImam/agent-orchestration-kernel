"""Executive Intelligence Engine for the JARVIS Kernel.

The ExecutiveEngine is the central orchestrator of the Kernel. It coordinates
configuration, memory, models, tools, workflows, events, security, and
capability adapters without depending on any external framework.
"""

from __future__ import annotations
import uuid

from typing import Any

from kernel.interfaces.capability_adapter import CapabilityTask, CapabilityResult
from kernel.interfaces.event_bus import EventBus
from kernel.interfaces.executive import (
    CapabilityService,
    ConfigProvider,
    ContextEngine,
    DecisionEngine,
    EnvironmentService,
    ExecutionEngine,
    IntentEngine,
    MemoryService,
    ModelService,
    ObservabilityService,
    PlanningEngine,
    PluginService,
    PolicyService,
    ReasoningEngine,
    RecoveryService,
    ToolService,
)
from kernel.interfaces.security_policy import SecurityPolicy
from kernel.interfaces.workflow_engine import WorkflowEngine
from kernel.intelligence.execution import COMPLETED, FAILED


class ExecutiveEngine:
    """Primary orchestration engine for the JARVIS Kernel."""

    def __init__(
        self,
        *,
        config: ConfigProvider,
        memory: MemoryService,
        models: ModelService,
        tools: ToolService,
        adapters: CapabilityService,
        workflows: WorkflowEngine,
        events: EventBus,
        security: SecurityPolicy,
        policy: PolicyService,
        context_engine: ContextEngine,
        intent_engine: IntentEngine,
        reasoning_engine: ReasoningEngine,
        decision_engine: DecisionEngine,
        planning_engine: PlanningEngine,
        execution_engine: ExecutionEngine,
        plugins: PluginService | None = None,
        recovery: RecoveryService | None = None,
        observability: ObservabilityService | None = None,
        digital_twin: EnvironmentService | None = None,
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
        self._context_engine = context_engine
        self._intent_engine = intent_engine
        self._reasoning_engine = reasoning_engine
        self._decision_engine = decision_engine
        self._planning_engine = planning_engine
        self._execution_engine = execution_engine
        self._plugins = plugins
        self._recovery = recovery
        self._observability = observability
        self._digital_twin = digital_twin

    async def execute_capability(
        self,
        intent: str,
        payload: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CapabilityResult:
        """Authorize and execute a capability task through the adapter manager."""

        await self._authorize_execution(intent)

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

    async def execute_request(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[CapabilityResult]:
        """Execute a high-level request through the intelligence pipeline.

        Flow: ContextEngine -> IntentEngine -> ReasoningEngine ->
              DecisionEngine -> PlanningEngine -> ExecutionEngine ->
              CapabilityAdapterManager -> Capability Adapter
        """
        if self._observability is not None:
            self._observability.record_request_started(objective)

        await self._events.publish(
            "request.started",
            {"objective": objective},
        )

        # Stage 1: Build execution context. The Context is runtime state
        # for the capability boundary: it is built once and passed through
        # the pipeline unchanged, consumed only by the ExecutionEngine.
        environment = context.get("environment") if context else None
        if self._digital_twin is not None:
            snapshot = self._digital_twin.get_snapshot()
            if snapshot is not None:
                if not isinstance(snapshot, dict):
                    snapshot = snapshot.to_dict()
                environment = {**environment, **snapshot} if environment else snapshot

        execution_context = self._context_engine.build(
            user_input=objective,
            conversation_id=context.get("conversation_id") if context else None,
            session_id=context.get("session_id") if context else None,
            working_memory=context.get("working_memory") if context else None,
            environment=environment,
            metadata=context.get("metadata") if context else None,
        )

        # Stage 2: Classify intent
        intent = self._intent_engine.classify(objective)

        # Stage 3: Perform reasoning
        reasoning = self._reasoning_engine.reason(intent)

        # Stage 4: Create decision
        decision = self._decision_engine.decide(intent, reasoning)

        # Stage 5: Generate plan
        plan = self._planning_engine.create_plan(decision)

        # Stage 6: Validate plan
        if not self._planning_engine.validate(plan):
            raise ValueError(f"Generated plan failed validation: {plan}")

        # Stage 7: Canonical authorization gate (security, then policy).
        # The SecurityPolicy contract is enforced on every execution path
        # through the same shared gate as execute_capability(). The gate
        # runs inside the same failure scope as execution: a denial closes
        # the request lifecycle (request.failed) and observability instead
        # of leaving the started request permanently open.
        # Stage 8: Execute via recovery if available, otherwise direct.
        # The ExecutionEngine is the execution boundary: it validates
        # capability availability for EXECUTE decisions and dispatches
        # through the CapabilityAdapterManager.
        try:
            await self._authorize_execution(intent.name)

            if self._recovery is None:
                execution = await self._execution_engine.execute(
                    plan, execution_context
                )
            else:
                execution = await self._recovery.async_execute_with_recovery(
                    self._execution_engine.execute,
                    plan,
                    execution_context,
                )
        except Exception:
            if self._observability is not None:
                self._observability.record_request_failed(objective)
            await self._events.publish(
                "request.failed",
                {
                    "objective": objective,
                    "success": False,
                },
            )
            raise

        # The request lifecycle must mirror the execution state. Only a
        # COMPLETED execution closes the request as completed; a FAILED
        # execution closes it as failed. PENDING (and any other
        # non-terminal status) leaves the request open: the request is
        # waiting, so no terminal lifecycle event is emitted and
        # observability does not record completion.
        if execution.status == COMPLETED:
            if self._observability is not None:
                self._observability.record_request_completed(objective)

            await self._events.publish(
                "request.completed",
                {
                    "objective": objective,
                    "success": execution.success,
                },
            )
        elif execution.status == FAILED:
            if self._observability is not None:
                self._observability.record_request_failed(objective)

            await self._events.publish(
                "request.failed",
                {
                    "objective": objective,
                    "success": False,
                },
            )

        # Convert execution to capability results for backward compatibility
        # The intelligence pipeline produces an Execution record; we wrap it
        # in a CapabilityResult for the existing API contract.
        return [
            CapabilityResult(
                success=execution.success,
                data={
                    "execution_id": execution.execution_id,
                    "plan_id": execution.plan_id,
                    "action": execution.action,
                    "status": execution.status,
                },
                error=None
                if execution.success
                else f"Execution failed: {execution.status}",
                metadata=execution.metadata,
            )
        ]

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

    async def _authorize_execution(self, intent: str) -> None:
        """Canonical authorization gate shared by every execution path.

        SecurityPolicy.authorize() runs first and records a security audit
        entry; the PolicyEngine rule check follows. Both execute_request()
        and execute_capability() enforce identical guarantees through this
        single gate, so no execution path can bypass the SecurityPolicy
        contract.
        """
        allowed = await self._security.authorize(
            subject="executive_engine",
            action=intent,
            resource="capability",
        )

        if not allowed:
            raise PermissionError(f"Execution denied for intent '{intent}'.")

        decision = self._policy.evaluate(intent)

        if not decision.allowed:
            raise PermissionError(decision.reason)

        if decision.requires_approval:
            raise PermissionError(
                f"Capability '{intent}' requires approval before execution."
            )

    async def health_check(self) -> dict[str, Any]:
        """Return the health of all Kernel managers."""
        health = {
            "memory": await self._memory.health_check(),
            "models": await self._models.health_check(),
            "tools": await self._tools.health_check(),
            "adapters": await self._adapters.health_check(),
            "workflows": await self._workflows.health_check(),
            "events": await self._events.health_check(),
            "security": await self._security.health_check(),
        }

        # Add intelligence engine health
        health["context_engine"] = await self._context_engine.health_check()
        health["intent_engine"] = await self._intent_engine.health_check()
        health["reasoning_engine"] = await self._reasoning_engine.health_check()
        health["decision_engine"] = await self._decision_engine.health_check()
        health["planning_engine"] = await self._planning_engine.health_check()
        health["execution_engine"] = await self._execution_engine.health_check()

        return health

    async def engine_info(self) -> dict[str, Any]:
        """Return runtime metadata describing the Executive Engine."""
        health = await self.health_check()
        return {
            "healthy": all(
                v if isinstance(v, bool) else v.get("healthy", False)
                for v in health.values()
            ),
            "context_engine": True,
            "intent_engine": True,
            "reasoning_engine": True,
            "decision_engine": True,
            "planning_engine": True,
            "execution_engine": True,
            "plugins": self._plugins is not None,
            "recovery": self._recovery is not None,
            "observability": self._observability is not None,
            "digital_twin": self._digital_twin is not None,
        }

    @property
    def config(self) -> ConfigProvider:
        return self._config

    @property
    def memory(self) -> MemoryService:
        return self._memory

    @property
    def models(self) -> ModelService:
        return self._models

    @property
    def tools(self) -> ToolService:
        return self._tools

    @property
    def adapters(self) -> CapabilityService:
        return self._adapters

    @property
    def workflows(self) -> WorkflowEngine:
        return self._workflows

    @property
    def events(self) -> EventBus:
        return self._events

    @property
    def security(self) -> SecurityPolicy:
        return self._security

    @property
    def policy(self) -> PolicyService:
        """Return the Kernel Policy Engine."""
        return self._policy

    @property
    def is_observability_enabled(self) -> bool:
        """Return whether observability support is configured."""
        return self._observability is not None

    @property
    def context_engine(self) -> ContextEngine:
        return self._context_engine

    @property
    def intent_engine(self) -> IntentEngine:
        return self._intent_engine

    @property
    def reasoning_engine(self) -> ReasoningEngine:
        return self._reasoning_engine

    @property
    def decision_engine(self) -> DecisionEngine:
        return self._decision_engine

    @property
    def planning_engine(self) -> PlanningEngine:
        return self._planning_engine

    @property
    def execution_engine(self) -> ExecutionEngine:
        return self._execution_engine

    @property
    def plugins(self) -> PluginService | None:
        return self._plugins

    @property
    def recovery(self) -> RecoveryService | None:
        return self._recovery

    @property
    def observability(self) -> ObservabilityService | None:
        return self._observability

    @property
    def digital_twin(self) -> EnvironmentService | None:
        return self._digital_twin

    @property
    def capabilities(self) -> dict[str, bool]:
        """Return which optional executive capabilities are configured."""
        return {
            "context_engine": True,
            "intent_engine": True,
            "reasoning_engine": True,
            "decision_engine": True,
            "planning_engine": True,
            "execution_engine": True,
            "plugins": self._plugins is not None,
            "recovery": self._recovery is not None,
            "observability": self._observability is not None,
            "digital_twin": self._digital_twin is not None,
        }
