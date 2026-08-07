

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ChangeType(str, Enum):
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    MODEL_SWITCHED = "model_switched"
    ADAPTER_ONLINE = "adapter_online"
    ADAPTER_OFFLINE = "adapter_offline"
    CPU_SPIKE = "cpu_spike"
    MEMORY_PRESSURE = "memory_pressure"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class EnvironmentChange:
    """Represents a detected change in the Kernel environment."""

    change_type: ChangeType
    description: str
    source: str
    change_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "description": self.description,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
        }