from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """
    Result of evaluating a capability request against the policy engine.
    """

    allowed: bool
    requires_approval: bool
    reason: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "metadata": self.metadata or {},
        }