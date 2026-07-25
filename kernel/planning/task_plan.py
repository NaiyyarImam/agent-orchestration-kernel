

"""Task plan model used by the Planning Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.planning.execution_step import ExecutionStep


@dataclass
class TaskPlan:
    plan_id: str
    goal: str
    steps: list[ExecutionStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ExecutionStep) -> None:
        self.steps.append(step)

    def step_count(self) -> int:
        return len(self.steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata,
        }