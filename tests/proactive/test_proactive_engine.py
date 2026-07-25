

"""Unit tests for the ProactiveEngine."""

from __future__ import annotations

from kernel.proactive.opportunity import Opportunity
from kernel.proactive.proactive_engine import ProactiveEngine
from kernel.proactive.proactive_rule import ProactiveRule, RuleAction
from kernel.proactive.proactive_signal import ProactiveSignal, SignalType
from kernel.proactive.suggestion import Suggestion


def test_register_rule_sorts_by_priority() -> None:
    engine = ProactiveEngine()

    low = ProactiveRule(
        name="Low",
        description="Low priority",
        signal_type="system",
        action=RuleAction.SUGGEST,
        priority=100,
    )
    high = ProactiveRule(
        name="High",
        description="High priority",
        signal_type="system",
        action=RuleAction.SUGGEST,
        priority=10,
    )

    engine.register_rule(low)
    engine.register_rule(high)

    assert engine.rules == [high, low]


def test_evaluate_generates_suggestion() -> None:
    engine = ProactiveEngine()
    engine.register_rule(
        ProactiveRule(
            name="System Suggestion",
            description="Create suggestion",
            signal_type="system",
            action=RuleAction.SUGGEST,
        )
    )

    signal = ProactiveSignal(
        source="kernel",
        signal_type=SignalType.SYSTEM,
        message="Started",
    )

    suggestions, opportunities = engine.evaluate(signal)

    assert len(suggestions) == 1
    assert len(opportunities) == 0
    assert isinstance(suggestions[0], Suggestion)
    assert suggestions[0].title == "System Suggestion"


def test_evaluate_generates_opportunity() -> None:
    engine = ProactiveEngine()
    engine.register_rule(
        ProactiveRule(
            name="Performance Opportunity",
            description="Optimize CPU",
            signal_type="performance",
            action=RuleAction.OPPORTUNITY,
        )
    )

    signal = ProactiveSignal(
        source="monitor",
        signal_type=SignalType.PERFORMANCE,
        message="High CPU",
        confidence=0.9,
    )

    suggestions, opportunities = engine.evaluate(signal)

    assert len(suggestions) == 0
    assert len(opportunities) == 1
    assert isinstance(opportunities[0], Opportunity)
    assert opportunities[0].title == "Performance Opportunity"


def test_evaluate_non_matching_rule() -> None:
    engine = ProactiveEngine()
    engine.register_rule(
        ProactiveRule(
            name="Security Rule",
            description="Alert",
            signal_type="security",
            action=RuleAction.ALERT,
        )
    )

    signal = ProactiveSignal(
        source="kernel",
        signal_type=SignalType.SYSTEM,
        message="Started",
    )

    suggestions, opportunities = engine.evaluate(signal)

    assert suggestions == []
    assert opportunities == []


def test_evaluate_disabled_rule() -> None:
    engine = ProactiveEngine()
    engine.register_rule(
        ProactiveRule(
            name="Disabled",
            description="Disabled rule",
            signal_type="system",
            action=RuleAction.SUGGEST,
            enabled=False,
        )
    )

    signal = ProactiveSignal(
        source="kernel",
        signal_type=SignalType.SYSTEM,
        message="Started",
    )

    suggestions, opportunities = engine.evaluate(signal)

    assert suggestions == []
    assert opportunities == []