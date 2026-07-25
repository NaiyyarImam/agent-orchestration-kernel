

"""Execution step model used by the Planning Engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ExecutionStep:
    step_id: str
    adapter: str
    intent: str
    payload: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "adapter": self.adapter,
            "intent": self.intent,
            "payload": self.payload,
            "description": self.description,
            "optional": self.optional,
        }