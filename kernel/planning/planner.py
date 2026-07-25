

"""Planning Engine for converting high-level goals into executable task plans."""

from __future__ import annotations

import uuid

from kernel.planning.execution_step import ExecutionStep
from kernel.planning.task_plan import TaskPlan


class Planner:
    def create_plan(self, goal: str) -> TaskPlan:
        plan = TaskPlan(
            plan_id=str(uuid.uuid4()),
            goal=goal
        )
        step = ExecutionStep(
            step_id="step-1",
            adapter="research",
            intent="research",
            payload={"query": goal},
            description="Research the requested goal.",
            optional=False
        )
        plan.add_step(step)
        return plan

    def supports_goal(self, goal: str) -> bool:
        return bool(goal.strip())