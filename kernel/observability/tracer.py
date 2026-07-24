

"""Tracing support for the Kernel Observability Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class TraceSpan:
    """Represents a traced execution span."""

    name: str
    span_id: str = field(default_factory=lambda: uuid4().hex)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float | None:
        """Return the span duration in seconds if finished."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def finish(self) -> "TraceSpan":
        """Return a completed copy of this span."""
        return TraceSpan(
            name=self.name,
            span_id=self.span_id,
            start_time=self.start_time,
            end_time=datetime.now(UTC),
            metadata=self.metadata.copy(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the span."""
        return {
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "metadata": self.metadata.copy(),
        }


class Tracer:
    """Collects execution spans."""

    def __init__(self) -> None:
        self._spans: list[TraceSpan] = []

    @property
    def spans(self) -> tuple[TraceSpan, ...]:
        """Return recorded spans."""
        return tuple(self._spans)

    def start_span(self, name: str, **metadata: Any) -> TraceSpan:
        """Start a new span."""
        span = TraceSpan(name=name, metadata=metadata)
        self._spans.append(span)
        return span

    def finish_span(self, span: TraceSpan) -> TraceSpan:
        """Finish an existing span."""
        completed = span.finish()
        index = self._spans.index(span)
        self._spans[index] = completed
        return completed

    def clear(self) -> None:
        """Remove all recorded spans."""
        self._spans.clear()

    def to_dict(self) -> list[dict[str, Any]]:
        """Serialize all spans."""
        return [span.to_dict() for span in self._spans]