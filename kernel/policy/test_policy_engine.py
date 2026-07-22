

import pytest

import json

try:
    import yaml
except ImportError:
    yaml = None

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


def test_wildcard_rule_matches_sub_intent() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True),
    ])

    decision = engine.evaluate("workspace.read")

    assert decision.allowed is True
    assert decision.intent == "workspace.*"


def test_exact_rule_takes_precedence_over_wildcard() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True),
        PolicyRule(intent="workspace.delete", allowed=False),
    ])

    decision = engine.evaluate("workspace.delete")

    assert decision.allowed is False
    assert decision.intent == "workspace.delete"


def test_most_specific_wildcard_rule_is_selected() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True),
        PolicyRule(intent="workspace.admin.*", allowed=False),
    ])

    decision = engine.evaluate("workspace.admin.delete")

    assert decision.allowed is False
    assert decision.intent == "workspace.admin.*"


def test_unknown_intent_without_matching_wildcard_is_denied() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True),
    ])

    decision = engine.evaluate("browser.search")

    assert decision.allowed is False
    assert decision.intent == "browser.search"


def test_higher_priority_wildcard_rule_is_selected() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True, priority=1),
        PolicyRule(intent="workspace.admin.*", allowed=False, priority=10),
    ])

    decision = engine.evaluate("workspace.admin.delete")

    assert decision.allowed is False
    assert decision.priority == 10
    assert decision.intent == "workspace.admin.*"


def test_more_specific_wildcard_wins_when_priorities_are_equal() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True, priority=5),
        PolicyRule(intent="workspace.admin.*", allowed=False, priority=5),
    ])

    decision = engine.evaluate("workspace.admin.delete")

    assert decision.allowed is False
    assert decision.intent == "workspace.admin.*"


def test_exact_match_overrides_higher_priority_wildcard() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True, priority=100),
        PolicyRule(intent="workspace.delete", allowed=False, priority=0),
    ])

    decision = engine.evaluate("workspace.delete")

    assert decision.allowed is False
    assert decision.intent == "workspace.delete"


def test_audit_log_records_exact_match() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="research.search", allowed=True),
    ])

    engine.evaluate("research.search")

    log = engine.audit_log()
    assert len(log) == 1
    assert log[0]["requested_intent"] == "research.search"
    assert log[0]["matched_intent"] == "research.search"
    assert log[0]["allowed"] is True


def test_audit_log_records_default_deny() -> None:
    engine = PolicyEngine()

    engine.evaluate("unknown.intent")

    log = engine.audit_log()
    assert len(log) == 1
    assert log[0]["requested_intent"] == "unknown.intent"
    assert log[0]["matched_intent"] == "unknown.intent"
    assert log[0]["allowed"] is False


def test_audit_log_records_wildcard_match() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="workspace.*", allowed=True),
    ])

    engine.evaluate("workspace.read")

    log = engine.audit_log()
    assert len(log) == 1
    assert log[0]["requested_intent"] == "workspace.read"
    assert log[0]["matched_intent"] == "workspace.*"


def test_clear_audit_removes_entries() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="research.search", allowed=True),
    ])

    engine.evaluate("research.search")
    assert len(engine.audit_log()) == 1

    engine.clear_audit()

    assert engine.audit_log() == ()


def test_audit_log_is_immutable() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="research.search", allowed=True),
    ])

    engine.evaluate("research.search")

    log = engine.audit_log()
    with pytest.raises(TypeError):
        log[0]["allowed"] = False


# New tests for loading policies from YAML, JSON, and dicts
@pytest.mark.skipif(yaml is None, reason="PyYAML is not installed")
def test_load_yaml_loads_rules(tmp_path) -> None:
    path = tmp_path / "policies.yaml"
    path.write_text(
        """
- intent: research.search
  allowed: true
- intent: workspace.delete
  allowed: false
""".strip(),
        encoding="utf-8",
    )

    engine = PolicyEngine()
    engine.load_yaml(path)

    assert engine.has_rule("research.search")
    assert engine.has_rule("workspace.delete")


def test_load_json_loads_rules(tmp_path) -> None:
    path = tmp_path / "policies.json"
    path.write_text(
        json.dumps([
            {"intent": "research.search", "allowed": True},
            {"intent": "workspace.delete", "allowed": False},
        ]),
        encoding="utf-8",
    )

    engine = PolicyEngine()
    engine.load_json(path)

    assert engine.has_rule("research.search")
    assert engine.has_rule("workspace.delete")


def test_load_dicts_replace_false_appends_rules() -> None:
    engine = PolicyEngine([
        PolicyRule(intent="memory.store", allowed=True),
    ])

    engine.load_dicts(
        [{"intent": "research.search", "allowed": True}],
        replace=False,
    )

    assert engine.has_rule("memory.store")
    assert engine.has_rule("research.search")


def test_load_json_requires_list(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"intent": "research.search"}), encoding="utf-8")

    engine = PolicyEngine()

    with pytest.raises(ValueError):
        engine.load_json(path)