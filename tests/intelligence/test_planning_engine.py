"""Unit tests for the PlanningEngine."""

from __future__ import annotations

import pytest

from kernel.intelligence.decision import Decision
from kernel.intelligence.plan import (
    DEFER,
    DENY,
    EXECUTE,
    PLAN_ACTIONS,
    REQUEST_CONFIRMATION,
    UNKNOWN,
    Plan,
)
from kernel.intelligence.planning_engine import (
    DECISION_TO_PLAN,
    DEFAULT_PRIORITY_LEVEL,
    PLAN_STEPS,
    PRIORITY_LEVELS,
    PlanningEngine,
)


def make_decision(
    action: str = "execute",
    confidence: float = 0.9,
    requires_confirmation: bool = False,
    metadata: dict | None = None,
) -> Decision:
    """Build a Decision for planning tests."""
    return Decision(
        action=action,
        confidence=confidence,
        requires_confirmation=requires_confirmation,
        explanation="explanation",
        metadata=metadata or {},
    )


@pytest.fixture
def engine() -> PlanningEngine:
    """Provide a PlanningEngine instance."""
    return PlanningEngine()


class TestCreatePlanMappings:
    """Tests for every Decision action mapping."""

    @pytest.mark.parametrize(
        ("decision_action", "expected_action", "expected_steps"),
        [
            ("execute", EXECUTE, PLAN_STEPS[EXECUTE]),
            (
                "ask_confirmation",
                REQUEST_CONFIRMATION,
                PLAN_STEPS[REQUEST_CONFIRMATION],
            ),
            (
                "ask_clarification",
                REQUEST_CONFIRMATION,
                PLAN_STEPS[REQUEST_CONFIRMATION],
            ),
            ("reject", DENY, PLAN_STEPS[DENY]),
            ("defer", DEFER, PLAN_STEPS[DEFER]),
            ("noop", UNKNOWN, PLAN_STEPS[UNKNOWN]),
        ],
    )
    def test_each_decision_action_maps_to_expected_plan(
        self,
        engine: PlanningEngine,
        decision_action: str,
        expected_action: str,
        expected_steps: tuple[str, ...],
    ) -> None:
        plan = engine.create_plan(make_decision(action=decision_action))

        assert plan.action == expected_action
        assert plan.steps == expected_steps

    def test_mapping_table_covers_all_decision_actions(self) -> None:
        from kernel.intelligence.decision import VALID_ACTIONS

        assert set(DECISION_TO_PLAN) == set(VALID_ACTIONS)

    def test_unknown_decision_action_falls_back_to_unknown(
        self, engine: PlanningEngine
    ) -> None:
        plan = engine.create_plan(make_decision(action="fly"))

        assert plan.action == UNKNOWN
        assert plan.steps == ("Unable to determine execution strategy",)

    def test_execute_steps_are_in_order(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision(action="execute"))

        assert plan.steps == (
            "Validate decision",
            "Prepare execution",
            "Execute task",
            "Record outcome",
        )

    def test_request_confirmation_steps(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision(action="ask_confirmation"))

        assert plan.steps == ("Request confirmation", "Await response")

    def test_deny_steps(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision(action="reject"))

        assert plan.steps == ("Reject request", "Explain denial")

    def test_returns_plan_instance(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision())

        assert isinstance(plan, Plan)


class TestCreatePlanMetadata:
    """Tests for metadata propagation."""

    def test_requires_confirmation_is_propagated(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(
            make_decision(action="execute", requires_confirmation=True)
        )

        assert plan.requires_confirmation is True

    def test_confidence_is_propagated(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision(action="execute", confidence=0.7))

        assert plan.confidence == 0.7

    def test_intent_name_is_propagated_into_goal(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(
            make_decision(action="execute", metadata={"intent": "code"})
        )

        assert plan.goal == "Resolve intent 'code' with action 'execute'"
        assert plan.metadata == {"decision_action": "execute", "intent": "code"}

    def test_missing_intent_metadata_defaults_to_unknown(
        self, engine: PlanningEngine
    ) -> None:
        plan = engine.create_plan(make_decision(action="execute"))

        assert plan.metadata["intent"] == "unknown"
        assert "unknown" in plan.goal


class TestCreatePlanPriority:
    """Tests for priority assignment."""

    @pytest.mark.parametrize(
        ("priority_label", "expected"),
        [("LOW", 0), ("NORMAL", 1), ("HIGH", 2)],
    )
    def test_priority_labels_map_to_integers(
        self,
        engine: PlanningEngine,
        priority_label: str,
        expected: int,
    ) -> None:
        plan = engine.create_plan(
            make_decision(action="execute", metadata={"priority": priority_label})
        )

        assert plan.priority == expected

    def test_missing_priority_defaults_to_normal(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision(action="execute"))

        assert plan.priority == PRIORITY_LEVELS[DEFAULT_PRIORITY_LEVEL] == 1

    def test_unrecognized_priority_defaults_to_normal(
        self, engine: PlanningEngine
    ) -> None:
        plan = engine.create_plan(
            make_decision(action="execute", metadata={"priority": "CRITICAL"})
        )

        assert plan.priority == 1


class TestCreatePlanInvalidInputs:
    """Tests for invalid input handling."""

    def test_none_decision_raises_value_error(self, engine: PlanningEngine) -> None:
        with pytest.raises(ValueError, match="decision is required"):
            engine.create_plan(None)  # type: ignore[arg-type]


class TestCreatePlanDeterminism:
    """Tests for deterministic plan creation."""

    def test_repeated_creation_is_stable(self, engine: PlanningEngine) -> None:
        decision = make_decision(
            action="execute",
            metadata={"intent": "code", "priority": "HIGH"},
        )

        first = engine.create_plan(decision)
        second = engine.create_plan(decision)
        third = engine.create_plan(decision)

        assert first == second == third
        assert first.action == EXECUTE
        assert first.priority == 2

    def test_returns_new_instance_each_call(self, engine: PlanningEngine) -> None:
        decision = make_decision()

        assert engine.create_plan(decision) is not engine.create_plan(decision)


class TestValidate:
    """Tests for plan validation."""

    def test_valid_plan_is_accepted(self, engine: PlanningEngine) -> None:
        plan = Plan(goal="goal", action=EXECUTE, priority=1, confidence=0.5)

        assert engine.validate(plan) is True

    def test_empty_goal_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="", action=EXECUTE)) is False

    def test_empty_action_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", action="")) is False

    def test_negative_confidence_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", confidence=-0.1)) is False

    def test_confidence_above_one_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", confidence=1.1)) is False

    def test_negative_priority_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", priority=-1)) is False

    def test_zero_confidence_is_accepted(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", confidence=0.0)) is True

    def test_maximum_confidence_is_accepted(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", confidence=1.0)) is True

    def test_zero_priority_is_accepted(self, engine: PlanningEngine) -> None:
        assert engine.validate(Plan(goal="goal", priority=0)) is True

    def test_none_plan_is_rejected(self, engine: PlanningEngine) -> None:
        assert engine.validate(None) is False  # type: ignore[arg-type]


class TestExplain:
    """Tests for explanation generation."""

    def test_explain_describes_plan(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(
            make_decision(action="execute", metadata={"intent": "code"})
        )

        explanation = engine.explain(plan)

        assert "Resolve intent 'code'" in explanation
        assert "action 'execute'" in explanation
        assert "4 steps" in explanation
        assert "priority 1" in explanation
        assert "confidence 0.9" in explanation

    def test_explain_is_deterministic(self, engine: PlanningEngine) -> None:
        plan = engine.create_plan(make_decision())

        assert engine.explain(plan) == engine.explain(plan)

    def test_explain_with_none_plan_raises_value_error(
        self, engine: PlanningEngine
    ) -> None:
        with pytest.raises(ValueError, match="plan is required"):
            engine.explain(None)  # type: ignore[arg-type]


class TestSupports:
    """Tests for the supports helper."""

    def test_supports_returns_all_plan_actions(self, engine: PlanningEngine) -> None:
        assert engine.supports() == PLAN_ACTIONS

    def test_supports_result_is_a_collection(self, engine: PlanningEngine) -> None:
        supported = engine.supports()

        assert isinstance(supported, frozenset)
        assert EXECUTE in supported
        assert REQUEST_CONFIRMATION in supported
        assert DEFER in supported
        assert DENY in supported
        assert UNKNOWN in supported

    def test_supports_is_deterministic(self, engine: PlanningEngine) -> None:
        assert engine.supports() == engine.supports()


class TestHealthCheck:
    """Tests for the engine health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, engine: PlanningEngine) -> None:
        assert await engine.health_check() == {"healthy": True}


class TestConstants:
    """Tests for engine constants."""

    def test_priority_levels_are_defined(self) -> None:
        assert PRIORITY_LEVELS == {"LOW": 0, "NORMAL": 1, "HIGH": 2}

    def test_plan_steps_cover_all_plan_actions(self) -> None:
        assert set(PLAN_STEPS) == set(PLAN_ACTIONS)
