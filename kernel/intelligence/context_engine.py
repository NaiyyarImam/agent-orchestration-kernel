"""Deterministic Context Engine for the Kernel Intelligence Layer.

The ContextEngine constructs and evolves the execution Context that
precedes Intent, Reasoning, and Decision. It never executes work, never
calls adapters or the Executive Engine, and makes no LLM or network
calls; it only builds and combines immutable state. The engine is
deliberately data-driven and dependency-free so a future semantic layer
can influence context construction without changing the public API.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Final

from kernel.intelligence.context import Context

# Context fields that are replaced wholesale on update.
SCALAR_FIELDS: Final[tuple[str, ...]] = (
    "user_input",
    "conversation_id",
    "session_id",
    "timestamp",
)

# Context fields that are merged recursively on update.
DICT_FIELDS: Final[tuple[str, ...]] = (
    "working_memory",
    "environment",
    "metadata",
)

# Capabilities this engine supports. Context is a prerequisite layer,
# so the only capability it can serve is context construction itself.
SUPPORTED_CAPABILITIES: Final[frozenset[str]] = frozenset({"context"})


def _merge_dicts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries, with right winning conflicts."""
    merged = dict(left)
    for key, value in right.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


class ContextEngine:
    """Deterministic builder and combiner of immutable Context objects."""

    def build(
        self,
        user_input: str,
        conversation_id: str | None = None,
        session_id: str | None = None,
        timestamp: datetime | None = None,
        working_memory: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Context:
        """Construct a new Context from the supplied information."""
        if not isinstance(user_input, str):
            raise ValueError("user_input must be a string")
        return Context(
            user_input=user_input,
            conversation_id=conversation_id,
            session_id=session_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            working_memory=deepcopy(working_memory) if working_memory else {},
            environment=deepcopy(environment) if environment else {},
            metadata=deepcopy(metadata) if metadata else {},
        )

    def update(self, context: Context, **changes: Any) -> Context:
        """Return a new Context with updated fields.

        Scalar fields are replaced; dictionary fields are merged
        recursively. The original Context is never mutated, and None
        dictionary values are ignored.
        """
        if context is None:
            raise ValueError("context is required")

        unknown = set(changes) - set(SCALAR_FIELDS + DICT_FIELDS)
        if unknown:
            raise ValueError(f"Unknown context field '{sorted(unknown)[0]}'")

        values: dict[str, Any] = {}
        for name in SCALAR_FIELDS:
            if name in changes:
                values[name] = changes[name]
        for name in DICT_FIELDS:
            value = changes.get(name)
            if value is not None:
                values[name] = _merge_dicts(getattr(context, name), value)

        if not values:
            return context

        return Context(
            user_input=values.get("user_input", context.user_input),
            conversation_id=values.get("conversation_id", context.conversation_id),
            session_id=values.get("session_id", context.session_id),
            timestamp=values.get("timestamp", context.timestamp),
            working_memory=values.get("working_memory", context.working_memory),
            environment=values.get("environment", context.environment),
            metadata=values.get("metadata", context.metadata),
        )

    def merge(self, first: Context, second: Context) -> Context:
        """Merge two Context objects into a new one.

        The second Context wins on conflicting values; its non-None
        identifiers override the first, and working memory, environment,
        and metadata are merged recursively.
        """
        if first is None or second is None:
            raise ValueError("contexts are required")
        return Context(
            user_input=second.user_input,
            conversation_id=second.conversation_id or first.conversation_id,
            session_id=second.session_id or first.session_id,
            timestamp=second.timestamp,
            working_memory=_merge_dicts(first.working_memory, second.working_memory),
            environment=_merge_dicts(first.environment, second.environment),
            metadata=_merge_dicts(first.metadata, second.metadata),
        )

    def supports(self, capability: str) -> bool:
        """Return True if the capability is supported."""
        return capability in SUPPORTED_CAPABILITIES

    async def health_check(self) -> dict[str, bool]:
        """Return the health status of the engine."""
        return {"healthy": True}

    def explain(self, context: Context) -> str:
        """Return a human-readable description of the context."""
        if context is None:
            raise ValueError("context is required")
        conversation = context.conversation_id or "unknown"
        session = context.session_id or "unknown"
        return (
            f"Context for input '{context.user_input}' in conversation "
            f"'{conversation}' and session '{session}' with "
            f"{len(context.working_memory)} working memory, "
            f"{len(context.environment)} environment, and "
            f"{len(context.metadata)} metadata entries."
        )
