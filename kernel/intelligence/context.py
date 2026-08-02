"""Context model for the Kernel Intelligence Layer."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Context:
    """Complete execution context for the Kernel Intelligence Layer.

    A Context captures everything the Kernel knows before an Intent is
    classified and reasoned about: the raw user input, conversation and
    session identifiers, the timestamp, working memory, environment
    details, and arbitrary metadata. It is immutable so downstream
    layers can rely on a stable snapshot of the execution state.
    """

    user_input: str
    conversation_id: str | None = None
    session_id: str | None = None
    timestamp: datetime = field(default_factory=_now)
    working_memory: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the context."""
        return {
            "user_input": self.user_input,
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "working_memory": deepcopy(self.working_memory),
            "environment": deepcopy(self.environment),
            "metadata": deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Context:
        """Reconstruct a context from its serialized form."""
        return cls(
            user_input=data["user_input"],
            conversation_id=data.get("conversation_id"),
            session_id=data.get("session_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            working_memory=deepcopy(data.get("working_memory", {})),
            environment=deepcopy(data.get("environment", {})),
            metadata=deepcopy(data.get("metadata", {})),
        )
