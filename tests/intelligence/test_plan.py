"""Unit tests for the Plan model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.intelligence.plan import (
    DEFER,
    DENY,
    EXECUTE,
    PLAN_ACTIONS,
    REQUEST_CONFIRMATION,
    UNKNOWN,
    Plan,
)


class TestPlanConstruction:
    """Tests for Plan construction."""

    def test_construct_with_all_fields(self) -> None:
        plan = Plan(
            goal="Resolve intent 'code'",
            action=EXECUTE,
            priority=2,
            requires_confirmation=False,
            confidence=0.9,
            steps=("Validate decision", "Execute task"),
            metadata={"decision_action": "execute"},
        )

        assert plan.goal == "Resolve intent 'code'"
        assert plan.action == EXECUTE
        assert plan.priority == 2
        assert plan.requires_confirmation is False
        assert plan.confidence == 0.9
        assert plan.steps == ("Validate decision", "Execute task")
        assert plan.metadata == {"decision_action": "execute"}

    def test_goal_is_required(self) -> None:
        with pytest.raises(TypeError):
            Plan()  # type: ignore[call-arg]

    def test_defaults_are_applied(self) -> None:
        plan = Plan(goal="Resolve intent 'chat'")

        assert plan.action == UNKNOWN
        assert plan.priority == 0
        assert plan.requires_confirmation is False
        assert plan.confidence == 0.0
        assert plan.steps == ()
        assert plan.metadata == {}


class TestPlanImmutability:
    """Tests for Plan immutability."""

    def test_plan_is_immutable(self) -> None:
        plan = Plan(goal="goal")

        with pytest.raises(FrozenInstanceError):
            plan.goal = "changed"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.action = EXECUTE  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.priority = 1  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.requires_confirmation = True  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.confidence = 0.5  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.steps = ("step",)  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            plan.metadata = {"a": 1}  # type: ignore[misc]


class TestPlanEquality:
    """Tests for Plan value equality."""

    def test_equal_plans_are_equal(self) -> None:
        first = Plan(goal="goal", action=EXECUTE, priority=2, confidence=0.9)
        second = Plan(goal="goal", action=EXECUTE, priority=2, confidence=0.9)

        assert first == second

    def test_different_goal_is_not_equal(self) -> None:
        assert Plan(goal="a") != Plan(goal="b")

    def test_different_action_is_not_equal(self) -> None:
        assert Plan(goal="g", action=EXECUTE) != Plan(goal="g", action=DEFER)

    def test_different_priority_is_not_equal(self) -> None:
        assert Plan(goal="g", priority=0) != Plan(goal="g", priority=1)

    def test_different_steps_is_not_equal(self) -> None:
        assert Plan(goal="g", steps=("a",)) != Plan(goal="g", steps=("b",))

    def test_different_metadata_is_not_equal(self) -> None:
        first = Plan(goal="g", metadata={"a": 1})
        second = Plan(goal="g", metadata={"a": 2})

        assert first != second


class TestPlanSerialization:
    """Tests for Plan serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        plan = Plan(
            goal="goal",
            action=DENY,
            priority=1,
            requires_confirmation=True,
            confidence=0.8,
            steps=("Reject request", "Explain denial"),
            metadata={"decision_action": "reject"},
        )

        assert plan.to_dict() == {
            "goal": "goal",
            "action": DENY,
            "priority": 1,
            "requires_confirmation": True,
            "confidence": 0.8,
            "steps": ["Reject request", "Explain denial"],
            "metadata": {"decision_action": "reject"},
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Plan(
            goal="goal",
            action=REQUEST_CONFIRMATION,
            priority=0,
            requires_confirmation=True,
            confidence=0.6,
            steps=("Request confirmation", "Await response"),
            metadata={"decision_action": "ask_confirmation"},
        )

        restored = Plan.from_dict(original.to_dict())

        assert restored == original

    def test_from_dict_without_optional_keys_defaults(self) -> None:
        plan = Plan.from_dict({"goal": "goal"})

        assert plan.action == UNKNOWN
        assert plan.priority == 0
        assert plan.requires_confirmation is False
        assert plan.confidence == 0.0
        assert plan.steps == ()
        assert plan.metadata == {}

    def test_steps_are_converted_to_tuple_on_deserialization(self) -> None:
        plan = Plan.from_dict({"goal": "goal", "steps": ["a", "b"]})

        assert plan.steps == ("a", "b")
        assert isinstance(plan.steps, tuple)

    def test_steps_are_serialized_as_list(self) -> None:
        plan = Plan(goal="goal", steps=("a", "b"))

        assert plan.to_dict()["steps"] == ["a", "b"]
        assert isinstance(plan.to_dict()["steps"], list)


class TestPlanSteps:
    """Tests for plan execution steps."""

    def test_steps_are_an_immutable_tuple(self) -> None:
        plan = Plan(goal="goal", steps=("Validate decision", "Execute task"))

        assert isinstance(plan.steps, tuple)
        with pytest.raises(TypeError):
            plan.steps[0] = "mutated"  # type: ignore[index]


class TestPlanConstants:
    """Tests for plan action constants."""

    def test_plan_actions_contains_all_outcomes(self) -> None:
        assert PLAN_ACTIONS == {
            EXECUTE,
            REQUEST_CONFIRMATION,
            DEFER,
            DENY,
            UNKNOWN,
        }

    def test_plan_actions_are_unique_strings(self) -> None:
        assert len(PLAN_ACTIONS) == 5
        assert all(isinstance(action, str) for action in PLAN_ACTIONS)
