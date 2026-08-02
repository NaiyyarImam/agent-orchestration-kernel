"""Unit tests for the DecisionEngine."""

from __future__ import annotations

import pytest

from kernel.intelligence.decision import (
    ASK_CLARIFICATION,
    ASK_CONFIRMATION,
    DEFER,
    EXECUTE,
    NOOP,
    REJECT,
    VALID_ACTIONS,
    Decision,
)
from kernel.intelligence.decision_engine import (
    ACTION_EXPLANATIONS,
    DEFERRED_CAPABILITIES,
    HIGH_CONFIDENCE_THRESHOLD,
    UNSAFE_CAPABILITIES,
    DecisionEngine,
)
from kernel.intelligence.intent import Intent
from kernel.intelligence.reasoning import Reasoning


def make_intent(name: str = "chat", confidence: float = 0.9) -> Intent:
    """Build an Intent for decision tests."""
    return Intent(name=name, confidence=confidence)


def make_reasoning(
    capability: str = "chat",
    priority: str = "LOW",
    requires_confirmation: bool = False,
) -> Reasoning:
    """Build a Reasoning object for decision tests."""
    return Reasoning(
        intent_name=capability,
        capability=capability,
        explanation="explanation",
        priority=priority,
        requires_confirmation=requires_confirmation,
    )


@pytest.fixture
def engine() -> DecisionEngine:
    """Provide a DecisionEngine instance."""
    return DecisionEngine()


class TestDecideExecute:
    """Tests for the execute path."""

    def test_high_confidence_without_confirmation_executes(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(make_intent(), make_reasoning())

        assert decision.action == EXECUTE
        assert decision.requires_confirmation is False
        assert decision.confidence == 0.9

    def test_boundary_confidence_executes(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(confidence=HIGH_CONFIDENCE_THRESHOLD), make_reasoning()
        )

        assert decision.action == EXECUTE

    def test_code_intent_executes_high_priority(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(name="code", confidence=0.9),
            make_reasoning(capability="coding", priority="HIGH"),
        )

        assert decision.action == EXECUTE

    def test_returns_decision_instance(self, engine: DecisionEngine) -> None:
        decision = engine.decide(make_intent(), make_reasoning())

        assert isinstance(decision, Decision)


class TestDecideConfirmation:
    """Tests for the ask_confirmation path."""

    def test_confirmation_required_asks_confirmation(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(),
            make_reasoning(capability="workspace", requires_confirmation=True),
        )

        assert decision.action == ASK_CONFIRMATION
        assert decision.requires_confirmation is True

    def test_workspace_reasoning_asks_confirmation(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(name="workspace", confidence=0.9),
            make_reasoning(
                capability="workspace", priority="NORMAL", requires_confirmation=True
            ),
        )

        assert decision.action == ASK_CONFIRMATION
        assert decision.confidence == 0.9


class TestDecideClarification:
    """Tests for the ask_clarification path."""

    def test_low_confidence_asks_clarification(self, engine: DecisionEngine) -> None:
        decision = engine.decide(make_intent(confidence=0.4), make_reasoning())

        assert decision.action == ASK_CLARIFICATION
        assert decision.requires_confirmation is False

    def test_below_threshold_asks_clarification(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(confidence=HIGH_CONFIDENCE_THRESHOLD - 0.01),
            make_reasoning(),
        )

        assert decision.action == ASK_CLARIFICATION

    def test_low_confidence_wins_over_confirmation(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(confidence=0.5),
            make_reasoning(capability="workspace", requires_confirmation=True),
        )

        assert decision.action == ASK_CLARIFICATION

    def test_decision_preserves_intent_confidence(self, engine: DecisionEngine) -> None:
        decision = engine.decide(make_intent(confidence=0.3), make_reasoning())

        assert decision.confidence == 0.3


class TestSafetySets:
    """Tests for the unsafe and deferred capability sets."""

    def test_unsafe_capabilities_are_defined(self) -> None:
        assert UNSAFE_CAPABILITIES == {"system", "admin", "exec", "delete"}

    def test_deferred_capabilities_are_defined(self) -> None:
        assert DEFERRED_CAPABILITIES == {"background", "scheduled", "defer"}

    def test_safety_sets_do_not_overlap_with_known_capabilities(self) -> None:
        known = {"chat", "research", "coding", "memory", "workspace", "browser"}

        assert UNSAFE_CAPABILITIES.isdisjoint(known)
        assert DEFERRED_CAPABILITIES.isdisjoint(known)


class TestDecideReject:
    """Tests for the rejection path."""

    def test_unsafe_capability_is_rejected(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(), make_reasoning(capability="system", priority="HIGH")
        )

        assert decision.action == REJECT
        assert decision.requires_confirmation is False

    def test_unsafe_beats_high_confidence(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(confidence=0.9), make_reasoning(capability="exec")
        )

        assert decision.action == REJECT

    def test_unsafe_beats_low_confidence(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(confidence=0.1), make_reasoning(capability="admin")
        )

        assert decision.action == REJECT


class TestDecideDefer:
    """Tests for the defer path."""

    def test_deferred_capability_is_deferred(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(), make_reasoning(capability="scheduled", priority="LOW")
        )

        assert decision.action == DEFER
        assert decision.requires_confirmation is False

    def test_defer_beats_low_confidence(self, engine: DecisionEngine) -> None:
        decision = engine.decide(
            make_intent(confidence=0.2), make_reasoning(capability="background")
        )

        assert decision.action == DEFER


class TestDecideNoop:
    """Tests for the noop path."""

    def test_missing_intent_is_noop(self, engine: DecisionEngine) -> None:
        decision = engine.decide(None, make_reasoning())

        assert decision.action == NOOP
        assert decision.confidence == 0.0
        assert decision.requires_confirmation is False
        assert decision.metadata == {}

    def test_missing_intent_and_reasoning_is_noop(self, engine: DecisionEngine) -> None:
        decision = engine.decide(None, None)

        assert decision.action == NOOP

    def test_noop_explanation(self, engine: DecisionEngine) -> None:
        decision = engine.decide(None, make_reasoning())

        assert decision.explanation == ACTION_EXPLANATIONS[NOOP]


class TestDecideInvalidInputs:
    """Tests for invalid input handling."""

    def test_missing_reasoning_raises_value_error(self, engine: DecisionEngine) -> None:
        with pytest.raises(ValueError, match="reasoning is required"):
            engine.decide(make_intent(), None)  # type: ignore[arg-type]


class TestDecideExplanation:
    """Tests for explanation generation."""

    def test_explanation_matches_canned_sentence(self, engine: DecisionEngine) -> None:
        decision = engine.decide(make_intent(), make_reasoning())

        assert decision.explanation == (
            "Executing the intent directly. Intent 'chat' resolved to "
            "capability 'chat' with confidence 0.9."
        )

    def test_explanation_mentions_intent_and_capability(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(name="code"),
            make_reasoning(capability="coding", priority="HIGH"),
        )

        assert "code" in decision.explanation
        assert "coding" in decision.explanation

    def test_explanation_is_not_empty_for_every_path(
        self, engine: DecisionEngine
    ) -> None:
        decisions = [
            engine.decide(make_intent(), make_reasoning()),
            engine.decide(
                make_intent(),
                make_reasoning(capability="workspace", requires_confirmation=True),
            ),
            engine.decide(make_intent(confidence=0.4), make_reasoning()),
            engine.decide(make_intent(), make_reasoning(capability="system")),
            engine.decide(make_intent(), make_reasoning(capability="scheduled")),
            engine.decide(None, make_reasoning()),
        ]

        for decision in decisions:
            assert decision.explanation
            assert decision.explanation.startswith(ACTION_EXPLANATIONS[decision.action])


class TestDecideMetadata:
    """Tests for decision metadata."""

    def test_metadata_includes_intent_capability_priority(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(name="code"),
            make_reasoning(capability="coding", priority="HIGH"),
        )

        assert decision.metadata == {
            "intent": "code",
            "capability": "coding",
            "priority": "HIGH",
        }

    def test_metadata_preserved_for_rejected_decisions(
        self, engine: DecisionEngine
    ) -> None:
        decision = engine.decide(
            make_intent(name="memory"), make_reasoning(capability="delete")
        )

        assert decision.metadata == {
            "intent": "memory",
            "capability": "delete",
            "priority": "LOW",
        }


class TestDecideDeterminism:
    """Tests for deterministic repeated decision making."""

    def test_repeated_decisions_are_stable(self, engine: DecisionEngine) -> None:
        intent = make_intent(name="code", confidence=0.9)
        reasoning = make_reasoning(capability="coding", priority="HIGH")

        first = engine.decide(intent, reasoning)
        second = engine.decide(intent, reasoning)
        third = engine.decide(intent, reasoning)

        assert first == second == third
        assert first.action == EXECUTE

    def test_repeated_noop_is_stable(self, engine: DecisionEngine) -> None:
        assert engine.decide(None, make_reasoning()) == engine.decide(
            None, make_reasoning()
        )

    def test_returns_new_instance_each_call(self, engine: DecisionEngine) -> None:
        intent = make_intent()
        reasoning = make_reasoning()

        assert engine.decide(intent, reasoning) is not engine.decide(intent, reasoning)


class TestConfidenceBoundaries:
    """Tests for confidence threshold boundaries."""

    def test_threshold_constant(self) -> None:
        assert HIGH_CONFIDENCE_THRESHOLD == 0.7

    def test_confidence_at_threshold_is_high(self, engine: DecisionEngine) -> None:
        assert (
            engine.decide(make_intent(confidence=0.7), make_reasoning()).action
            == EXECUTE
        )

    def test_confidence_just_below_threshold_is_low(
        self, engine: DecisionEngine
    ) -> None:
        assert (
            engine.decide(make_intent(confidence=0.699), make_reasoning()).action
            == ASK_CLARIFICATION
        )

    def test_confidence_just_above_threshold_is_high(
        self, engine: DecisionEngine
    ) -> None:
        assert (
            engine.decide(make_intent(confidence=0.701), make_reasoning()).action
            == EXECUTE
        )


class TestExplain:
    """Tests for the explain helper."""

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (EXECUTE, "Executing the intent directly."),
            (ASK_CONFIRMATION, "Asking the user to confirm before executing."),
            (ASK_CLARIFICATION, "Asking the user to clarify the intent."),
            (REJECT, "Rejecting the intent as unsafe."),
            (DEFER, "Deferring the intent to a later time."),
            (NOOP, "Taking no action."),
        ],
    )
    def test_explain_returns_sentence_for_every_action(
        self, engine: DecisionEngine, action: str, expected: str
    ) -> None:
        assert engine.explain(action) == expected

    def test_explain_unknown_action_raises_value_error(
        self, engine: DecisionEngine
    ) -> None:
        with pytest.raises(ValueError, match="Unknown decision action"):
            engine.explain("fly")  # type: ignore[arg-type]


class TestSupports:
    """Tests for the supports helper."""

    def test_supports_all_actions(self, engine: DecisionEngine) -> None:
        for action in VALID_ACTIONS:
            assert engine.supports(action) is True

    def test_supports_unknown_action(self, engine: DecisionEngine) -> None:
        assert engine.supports("fly") is False

    def test_supports_is_case_sensitive(self, engine: DecisionEngine) -> None:
        assert engine.supports("Execute") is False


class TestHealthCheck:
    """Tests for the engine health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self, engine: DecisionEngine) -> None:
        assert await engine.health_check() is True
