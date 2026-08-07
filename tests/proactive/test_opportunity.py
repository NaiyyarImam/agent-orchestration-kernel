"""Unit tests for the Opportunity model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.proactive.opportunity import Opportunity, OpportunitySeverity


def test_severity_values() -> None:
    assert OpportunitySeverity.LOW.value == "low"
    assert OpportunitySeverity.MEDIUM.value == "medium"
    assert OpportunitySeverity.HIGH.value == "high"
    assert OpportunitySeverity.CRITICAL.value == "critical"


def test_opportunity_defaults() -> None:
    opportunity = Opportunity(
        title="Idle GPU",
        description="GPU has been idle for 30 minutes",
    )

    assert opportunity.title == "Idle GPU"
    assert opportunity.description == "GPU has been idle for 30 minutes"
    assert opportunity.severity is OpportunitySeverity.MEDIUM
    assert opportunity.confidence == 1.0
    assert opportunity.opportunity_id
    assert opportunity.metadata == {}


def test_custom_values() -> None:
    opportunity = Opportunity(
        title="Memory pressure",
        description="Memory usage exceeds threshold",
        severity=OpportunitySeverity.CRITICAL,
        confidence=0.95,
        metadata={"component": "memory"},
    )

    assert opportunity.severity is OpportunitySeverity.CRITICAL
    assert opportunity.confidence == 0.95
    assert opportunity.metadata == {"component": "memory"}


def test_opportunity_is_frozen() -> None:
    opportunity = Opportunity(
        title="Idle GPU",
        description="GPU idle",
    )

    with pytest.raises(FrozenInstanceError):
        opportunity.title = "Changed"  # type: ignore[misc]


def test_to_dict() -> None:
    opportunity = Opportunity(
        title="Optimize cache",
        description="Cache hit rate is low",
        severity=OpportunitySeverity.HIGH,
        confidence=0.88,
        metadata={"cache": "primary"},
    )

    data = opportunity.to_dict()

    assert data["title"] == "Optimize cache"
    assert data["description"] == "Cache hit rate is low"
    assert data["severity"] == "high"
    assert data["confidence"] == 0.88
    assert data["metadata"] == {"cache": "primary"}
    assert data["opportunity_id"] == opportunity.opportunity_id
    assert isinstance(data["timestamp"], str)