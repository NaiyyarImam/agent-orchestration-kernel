

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class EnvironmentSnapshot:
    """Immutable point-in-time view of the Kernel environment."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_models: tuple[str, ...] = ()
    active_plugins: tuple[str, ...] = ()
    running_workflows: tuple[str, ...] = ()
    adapter_status: dict[str, str] = field(default_factory=dict)
    snapshot_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "active_models": list(self.active_models),
            "active_plugins": list(self.active_plugins),
            "running_workflows": list(self.running_workflows),
            "adapter_status": dict(self.adapter_status),
            "metadata": dict(self.metadata),
        }