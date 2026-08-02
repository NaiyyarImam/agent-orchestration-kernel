"""Deterministic Execution Engine for the Kernel Intelligence Layer.

The ExecutionEngine converts a Plan into an Execution record using a
fixed rule set: valid plans are recorded as completed, invalid plans as
failed. It never performs real work, never calls adapters, the Executive
Engine, or the kernel/planning module, and makes no LLM or network
calls; it only records the deterministic outcome. The behavior is
deliberately data-driven so a future semantic executor can replace the
deterministic logic without changing the public API.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final

from kernel.intelligence.execution import (
    COMPLETED,
    EXECUTION_STATUSES,
    FAILED,
    Execution,
)
from kernel.intelligence.plan import Plan
from kernel.intelligence.planning_engine import PlanningEngine

# Reused to determine plan validity so the definition lives in one place.
_PLANNING_ENGINE: Final[PlanningEngine] = PlanningEngine()


class ExecutionEngine:
    """Deterministic rule-based plan-to-execution recorder."""

    def execute(self, plan: Plan) -> Execution:
        """Record a deterministic Execution for the given plan.

        Invalid plans are recorded as failed; valid plans are recorded
        as completed. Nothing is actually executed by this engine.
        """
        signature = self._plan_signature(plan)
        valid = plan is not None and _PLANNING_ENGINE.validate(plan)
        action = plan.action if plan is not None else "unknown"
        goal = plan.goal if plan is not None else "unknown"

        return Execution(
            execution_id=f"exec-{signature}",
            plan_id=f"plan-{signature}",
            action=action,
            status=COMPLETED if valid else FAILED,
            success=valid,
            confidence=plan.confidence if plan is not None else 0.0,
            metadata={"plan_action": action, "goal": goal},
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
