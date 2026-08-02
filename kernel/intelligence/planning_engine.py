"""Deterministic Planning Engine for the Kernel Intelligence Layer.

The PlanningEngine converts a Decision into a Plan of concrete execution
steps using a fixed, data-driven rule set. It never executes work, never
calls adapters, the Executive Engine, or the kernel/planning module, and
makes no LLM or network calls; it only plans. The mappings are
deliberately data-driven so a future semantic planner can replace the
deterministic logic without changing the public API.
"""

from __future__ import annotations

from typing import Final

from kernel.intelligence.decision import Decision
from kernel.intelligence.plan import (
    DEFER,
    DENY,
    EXECUTE,
    PLAN_ACTIONS,
    REQUEST_CONFIRMATION,
    UNKNOWN,
    Plan,
)

# Decision action -> plan action. Keys mirror the Decision action
# constants in kernel.intelligence.decision; both ask_* outcomes pause
# for user input, so they share the request_confirmation plan.
DECISION_TO_PLAN: Final[dict[str, str]] = {
    "execute": EXECUTE,
    "ask_confirmation": REQUEST_CONFIRMATION,
    "ask_clarification": REQUEST_CONFIRMATION,
    "reject": DENY,
    "defer": DEFER,
    "noop": UNKNOWN,
}

# Plan action -> execution steps, in order.
PLAN_STEPS: Final[dict[str, tuple[str, ...]]] = {
    EXECUTE: (
        "Validate decision",
        "Prepare execution",
        "Execute task",
        "Record outcome",
    ),
    REQUEST_CONFIRMATION: (
        "Request confirmation",
        "Await response",
    ),
    DEFER: (
        "Record deferred action",
        "Schedule later execution",
    ),
    DENY: (
        "Reject request",
        "Explain denial",
    ),
    UNKNOWN: ("Unable to determine execution strategy",),
}

# Reasoning priority string -> plan priority integer.
PRIORITY_LEVELS: Final[dict[str, int]] = {
    "LOW": 0,
    "NORMAL": 1,
    "HIGH": 2,
}

DEFAULT_PRIORITY_LEVEL: Final[str] = "NORMAL"


class PlanningEngine:
    """Deterministic rule-based decision-to-plan converter."""

    def create_plan(self, decision: Decision) -> Plan:
        """Convert a Decision into a deterministic execution Plan.

        Unrecognized decision actions fall back to the unknown plan.
        """
        if decision is None:
            raise ValueError("decision is required")

        action = DECISION_TO_PLAN.get(decision.action, UNKNOWN)
        intent_name = str(decision.metadata.get("intent", "unknown"))
        priority = PRIORITY_LEVELS.get(
            str(decision.metadata.get("priority", DEFAULT_PRIORITY_LEVEL)),
            PRIORITY_LEVELS[DEFAULT_PRIORITY_LEVEL],
        )

        return Plan(
            goal=f"Resolve intent '{intent_name}' with action '{action}'",
            action=action,
            priority=priority,
            requires_confirmation=decision.requires_confirmation,
            confidence=decision.confidence,
            steps=PLAN_STEPS[action],
            metadata={
                "decision_action": decision.action,
                "intent": intent_name,
            },
        )

    @staticmethod
    def validate(plan: Plan) -> bool:
        """Return True only when the plan is structurally valid."""
        if plan is None:
            return False
        if not plan.goal or not plan.action:
            return False
        if not 0.0 <= plan.confidence <= 1.0:
            return False
        if plan.priority < 0:
            return False
        return True

    def supports(self) -> frozenset[str]:
        """Return the collection of supported planning capabilities."""
        return PLAN_ACTIONS

    async def health_check(self) -> dict[str, bool]:
        """Return the health status of the engine."""
        return {"healthy": True}

    def explain(self, plan: Plan) -> str:
        """Return a deterministic human-readable explanation of a plan."""
        if plan is None:
            raise ValueError("plan is required")
        return (
            f"Plan for '{plan.goal}' using action '{plan.action}' with "
            f"{len(plan.steps)} steps, priority {plan.priority}, and "
            f"confidence {plan.confidence}."
        )
