

"""Unit tests for the ProactiveRule model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.proactive.proactive_rule import ProactiveRule, RuleAction


def test_rule_action_values() -> None:
    assert RuleAction.IGNORE.value == "ignore"
    assert RuleAction.SUGGEST.value == "suggest"
    assert RuleAction.OPPORTUNITY.value == "opportunity"
    assert RuleAction.ALERT.value == "alert"


def test_rule_defaults() -> None:
    rule = ProactiveRule(
        name="System Rule",
        description="Handle system signals",
        signal_type="system",
        action=RuleAction.SUGGEST,
    )

    assert rule.name == "System Rule"
    assert rule.description == "Handle system signals"
    assert rule.signal_type == "system"
    assert rule.action is RuleAction.SUGGEST
    assert rule.enabled is True
    assert rule.priority == 100
    assert rule.confidence_threshold == 0.5
    assert rule.rule_id
    assert rule.metadata == {}


def test_applies_to() -> None:
    rule = ProactiveRule(
        name="Performance Rule",
        description="Detect high CPU",
        signal_type="performance",
        action=RuleAction.ALERT,
        confidence_threshold=0.8,
    )

    assert rule.applies_to("performance", 0.9) is True
    assert rule.applies_to("performance", 0.7) is False
    assert rule.applies_to("system", 0.9) is False


def test_rule_is_frozen() -> None:
    rule = ProactiveRule(
        name="Test",
        description="Frozen",
        signal_type="system",
        action=RuleAction.IGNORE,
    )

    with pytest.raises(FrozenInstanceError):
        rule.name = "Changed"  # type: ignore[misc]


def test_to_dict() -> None:
    rule = ProactiveRule(
        name="Security Rule",
        description="Handle security signals",
        signal_type="security",
        action=RuleAction.ALERT,
        priority=10,
        confidence_threshold=0.95,
        metadata={"team": "security"},
    )

    data = rule.to_dict()

    assert data["name"] == "Security Rule"
    assert data["description"] == "Handle security signals"
    assert data["signal_type"] == "security"
    assert data["action"] == "alert"
    assert data["enabled"] is True
    assert data["priority"] == 10
    assert data["confidence_threshold"] == 0.95
    assert data["metadata"] == {"team": "security"}
    assert data["rule_id"] == rule.rule_id
    assert isinstance(data["created_at"], str)