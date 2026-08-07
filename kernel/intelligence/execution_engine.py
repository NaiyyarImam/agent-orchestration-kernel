"""Execution Engine for the Kernel Intelligence Layer.

The ExecutionEngine is the execution boundary between the Intelligence
Layer and capability execution. It converts a Plan into an Execution
record: valid EXECUTE plans are dispatched to the CapabilityAdapterManager
through the injected CapabilityService port, and the adapter outcome is
recorded as the Execution Result. Invalid plans and non-execute actions
(confirmation, defer, deny, unknown) are recorded deterministically
without dispatching. The engine never instantiates adapters itself and
makes no LLM or network calls; dispatch is delegated exclusively to the
injected port so the Ports & Adapters boundary is preserved.

The engine is the sole consumer of the execution Context: it never feeds
Context back into intelligence stages. When a Context is supplied, the
CapabilityTask dispatched to the capability boundary is populated from
it — execution data (user input, working memory) in the payload, runtime
and environment information in the task context, and execution metadata
(conversation/session identifiers when present) in the task metadata.
The Context is never mutated.

Execution semantics: EXECUTE plans that dispatch reflect the adapter
result (COMPLETED/FAILED). Waiting plans — request_confirmation, defer,
and unknown (the ask_confirmation, ask_clarification, defer, and noop
decision outcomes) — are recorded as PENDING with success False because
the plan has been interpreted correctly but execution is waiting on an
external actor; nothing has executed, so completion is never faked.
Denial is a terminal outcome and remains COMPLETED.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Final

from kernel.interfaces.capability_adapter import CapabilityTask
from kernel.intelligence.context import Context
from kernel.intelligence.execution import (
    COMPLETED,
    EXECUTION_STATUSES,
    FAILED,
    PENDING,
    Execution,
)
from kernel.intelligence.plan import (
    DEFER,
    EXECUTE,
    REQUEST_CONFIRMATION,
    UNKNOWN,
    Plan,
)
from kernel.intelligence.planning_engine import PlanningEngine

if TYPE_CHECKING:
    from kernel.interfaces.executive import CapabilityService

# Plan actions that wait on an external actor (or are intentionally
# deferred): the plan has been interpreted correctly but execution has
# not happened, so the Execution is recorded as PENDING, never COMPLETED,
# and never successful.
WAITING_ACTIONS: Final[frozenset[str]] = frozenset(
    {REQUEST_CONFIRMATION, DEFER, UNKNOWN}
)


class ExecutionEngine:
    """Execution boundary between the Intelligence Layer and capability execution."""

    def __init__(self, capabilities: CapabilityService | None = None) -> None:
        """Configure the execution boundary.

        capabilities is the port to the CapabilityAdapterManager. When
        provided, EXECUTE plans are dispatched through it; when absent,
        valid plans are recorded deterministically without dispatching.
        """
        self._capabilities = capabilities

    async def execute(self, plan: Plan, context: Context | None = None) -> Execution:
        """Execute a plan through the capability boundary and record the outcome.

        Invalid plans are recorded as failed. EXECUTE plans are
        dispatched to the CapabilityAdapterManager through the injected
        CapabilityService port; the adapter result is recorded. Waiting
        plans (request_confirmation, defer, unknown) are recorded as
        PENDING without dispatching — the plan has been interpreted but
        execution is waiting on an external actor, so success is False.
        Denied plans are recorded as completed without dispatching.

        context carries the runtime state built before the intelligence
        stages. It is consumed only here, at the capability boundary, and
        is never mutated. When present, the dispatched CapabilityTask is
        populated from it; when absent, empty task fields are preserved.
        """
        signature = self._plan_signature(plan)
        valid = plan is not None and PlanningEngine.validate(plan)

        action = plan.action if plan is not None else "unknown"
        goal = plan.goal if plan is not None else "unknown"

        if not valid:
            return Execution(
                execution_id=f"exec-{signature}",
                plan_id=f"plan-{signature}",
                action=action,
                status=FAILED,
                success=False,
                confidence=plan.confidence if plan is not None else 0.0,
                metadata={"plan_action": action, "goal": goal},
            )

        if action == EXECUTE and self._capabilities is not None:
            return await self._execute_capability(plan, signature, context)

        if action in WAITING_ACTIONS:
            return Execution(
                execution_id=f"exec-{signature}",
                plan_id=f"plan-{signature}",
                action=action,
                status=PENDING,
                success=False,
                confidence=plan.confidence if plan is not None else 0.0,
                metadata={"plan_action": action, "goal": goal},
            )

        return Execution(
            execution_id=f"exec-{signature}",
            plan_id=f"plan-{signature}",
            action=action,
            status=COMPLETED,
            success=True,
            confidence=plan.confidence if plan is not None else 0.0,
            metadata={"plan_action": action, "goal": goal},
        )

    async def _execute_capability(
        self,
        plan: Plan,
        signature: str,
        context: Context | None,
    ) -> Execution:
        """Dispatch a valid EXECUTE plan to the capability boundary."""
        intent_name = str(plan.metadata.get("intent", "unknown"))

        if not self._capabilities.can_handle(intent_name):
            raise ValueError(f"Unknown capability: {intent_name}")

        payload: dict[str, Any] = {}
        task_context: dict[str, Any] = {}
        task_metadata: dict[str, Any] = {}

        if context is not None:
            payload = {
                "user_input": context.user_input,
                "working_memory": deepcopy(context.working_memory),
            }
            task_context = {
                "environment": deepcopy(context.environment),
                "timestamp": context.timestamp.isoformat(),
            }
            task_metadata.update(deepcopy(context.metadata))
            if context.conversation_id is not None:
                task_metadata["conversation_id"] = context.conversation_id
            if context.session_id is not None:
                task_metadata["session_id"] = context.session_id

        task_metadata.update(
            {
                "plan_id": f"plan-{signature}",
                "goal": plan.goal,
                "plan_action": plan.action,
            }
        )

        task = CapabilityTask(
            task_id=f"task-{signature}",
            intent=intent_name,
            payload=payload,
            context=task_context,
            metadata=task_metadata,
        )

        result = await self._capabilities.execute(task)

        metadata: dict[str, Any] = {
            "plan_action": plan.action,
            "goal": plan.goal,
            "capability": intent_name,
            "capability_result": result.data,
        }
        if result.metadata.get("adapter") is not None:
            metadata["adapter"] = result.metadata["adapter"]

        return Execution(
            execution_id=f"exec-{signature}",
            plan_id=f"plan-{signature}",
            action=plan.action,
            status=COMPLETED if result.success else FAILED,
            success=result.success,
            confidence=plan.confidence,
            metadata=metadata,
        )

    def validate(self, execution: Execution) -> bool:
        """Return True only when the execution record is structurally valid."""
        if execution is None:
            return False
        if not execution.execution_id or not execution.plan_id or not execution.action:
            return False
        if execution.status not in EXECUTION_STATUSES:
            return False
        if not 0.0 <= execution.confidence <= 1.0:
            return False
        return True

    def supports(self) -> frozenset[str]:
        """Return the collection of supported execution capabilities."""
        return EXECUTION_STATUSES

    async def health_check(self) -> dict[str, bool]:
        """Return the health status of the engine."""
        return {"healthy": True}

    def explain(self, execution: Execution) -> str:
        """Return a deterministic human-readable description of an execution."""
        if execution is None:
            raise ValueError("execution is required")
        return (
            f"Execution '{execution.execution_id}' for plan "
            f"'{execution.plan_id}' with action '{execution.action}' is "
            f"{execution.status} (success: {execution.success}) with "
            f"confidence {execution.confidence}."
        )

    @staticmethod
    def _plan_signature(plan: Plan) -> str:
        """Return a stable content signature for the plan."""
        if plan is None:
            return "unknown"
        payload = json.dumps(
            plan.to_dict(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]
