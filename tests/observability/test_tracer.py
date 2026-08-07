

"""Unit tests for the Tracer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.observability.tracer import TraceSpan, Tracer


def test_trace_span_defaults() -> None:
    span = TraceSpan(name="kernel")

    assert span.name == "kernel"
    assert span.span_id
    assert span.end_time is None
    assert span.duration is None
    assert span.metadata == {}


def test_trace_span_is_frozen() -> None:
    span = TraceSpan(name="kernel")

    with pytest.raises(FrozenInstanceError):
        span.name = "planner"  # type: ignore[misc]


def test_finish_returns_completed_span() -> None:
    span = TraceSpan(name="kernel")

    completed = span.finish()

    assert completed is not span
    assert completed.span_id == span.span_id
    assert completed.end_time is not None
    assert completed.duration is not None
    assert completed.duration >= 0


def test_to_dict() -> None:
    span = TraceSpan(name="kernel", metadata={"step": 1}).finish()

    data = span.to_dict()

    assert data["name"] == "kernel"
    assert data["span_id"] == span.span_id
    assert data["metadata"] == {"step": 1}
    assert isinstance(data["start_time"], str)
    assert isinstance(data["end_time"], str)


def test_start_span() -> None:
    tracer = Tracer()

    span = tracer.start_span("kernel", task="boot")

    assert span.name == "kernel"
    assert span.metadata == {"task": "boot"}
    assert tracer.spans == (span,)


def test_finish_span() -> None:
    tracer = Tracer()

    span = tracer.start_span("kernel")
    completed = tracer.finish_span(span)

    assert completed.end_time is not None
    assert tracer.spans == (completed,)


def test_spans_property() -> None:
    tracer = Tracer()

    tracer.start_span("one")
    tracer.start_span("two")

    spans = tracer.spans

    assert len(spans) == 2
    assert isinstance(spans, tuple)


def test_clear() -> None:
    tracer = Tracer()

    tracer.start_span("kernel")
    tracer.clear()

    assert tracer.spans == ()


def test_tracer_to_dict() -> None:
    tracer = Tracer()

    span = tracer.start_span("kernel")
    tracer.finish_span(span)

    data = tracer.to_dict()

    assert len(data) == 1
    assert data[0]["name"] == "kernel"
    assert data[0]["duration"] is not None