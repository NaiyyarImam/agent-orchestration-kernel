

"""Unit tests for the Suggestion model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.proactive.suggestion import Suggestion, SuggestionPriority


def test_priority_values() -> None:
    assert SuggestionPriority.LOW.value == "low"
    assert SuggestionPriority.MEDIUM.value == "medium"
    assert SuggestionPriority.HIGH.value == "high"
    assert SuggestionPriority.CRITICAL.value == "critical"


def test_suggestion_defaults() -> None:
    suggestion = Suggestion(
        title="Reload model",
        reason="Model is idle",
    )

    assert suggestion.title == "Reload model"
    assert suggestion.reason == "Model is idle"
    assert suggestion.priority is SuggestionPriority.MEDIUM
    assert suggestion.confidence == 1.0
    assert suggestion.suggestion_id
    assert suggestion.metadata == {}


def test_custom_values() -> None:
    suggestion = Suggestion(
        title="Warm cache",
        reason="Frequently accessed",
        priority=SuggestionPriority.HIGH,
        confidence=0.92,
        metadata={"component": "cache"},
    )

    assert suggestion.priority is SuggestionPriority.HIGH
    assert suggestion.confidence == 0.92
    assert suggestion.metadata == {"component": "cache"}


def test_suggestion_is_frozen() -> None:
    suggestion = Suggestion(
        title="Reload model",
        reason="Idle",
    )

    with pytest.raises(FrozenInstanceError):
        suggestion.title = "Changed"  # type: ignore[misc]


def test_to_dict() -> None:
    suggestion = Suggestion(
        title="Optimize workflow",
        reason="Repeated task detected",
        priority=SuggestionPriority.CRITICAL,
        confidence=0.99,
        metadata={"workflow": "daily"},
    )

    data = suggestion.to_dict()

    assert data["title"] == "Optimize workflow"
    assert data["reason"] == "Repeated task detected"
    assert data["priority"] == "critical"
    assert data["confidence"] == 0.99
    assert data["metadata"] == {"workflow": "daily"}
    assert data["suggestion_id"] == suggestion.suggestion_id
    assert isinstance(data["timestamp"], str)