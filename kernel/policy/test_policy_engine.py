

import pytest

from kernel.policy import PolicyEngine, PolicyRule


def test_register_and_get_rule() -> None:
    engine = PolicyEngine()
    rule = PolicyRule(intent="research.search", allowed=True)

    engine.register(rule)

    assert engine.get_rule("research.search") == rule


def test_register_replaces_existing_rule() -> None:
    engine = PolicyEngine()
    engine.register(PolicyRule(intent="research.search", allowed=True))
    replacement = PolicyRule(intent="research.search", allowed=False)

    engine.register(replacement)

    assert engine.get_rule("research.search") == replacement


def test_unregister_rule() -> None:
    engine = PolicyEngine([PolicyRule(intent="coding.run")])

    engine.unregister("coding.run")

    assert engine.get_rule("coding.run") is None


def test_default_deny_for_unknown_intent() -> None:
    engine = PolicyEngine()

    decision = engine.evaluate("unknown.intent")

    assert decision.allowed is False
    assert decision.intent == "unknown.intent"


def test_empty_intent_validation() -> None:
    with pytest.raises(ValueError):
        PolicyRule(intent="   ")

    engine = PolicyEngine()
    with pytest.raises(ValueError):
        engine.evaluate("")


def test_intent_is_normalized() -> None:
    rule = PolicyRule(intent="  Research.Search  ")

    assert rule.intent == "research.search"


def test_metadata_is_immutable() -> None:
    rule = PolicyRule(intent="research.search", metadata={"x": 1})

    with pytest.raises(TypeError):
        rule.metadata["y"] = 2


def test_has_rule_and_contains() -> None:
    engine = PolicyEngine()
    engine.register(PolicyRule(intent="research.search"))

    assert engine.has_rule("research.search")
    assert "research.search" in engine


def test_clear_removes_all_rules() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="a"),
        PolicyRule(intent="b"),
    ])

    engine.clear()

    assert len(engine) == 0


def test_len_returns_rule_count() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="a"),
        PolicyRule(intent="b"),
    ])

    assert len(engine) == 2