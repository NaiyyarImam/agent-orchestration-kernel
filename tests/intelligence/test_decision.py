"""Unit tests for the Decision model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

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


class TestDecisionConstruction:
    """Tests for Decision construction."""

    def test_construct_with_all_fields(self) -> None:
        decision = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="Executing the intent directly.",
            metadata={"intent": "code"},
        )

        assert decision.action == EXECUTE
        assert decision.confidence == 0.9
        assert decision.requires_confirmation is False
        assert decision.explanation == "Executing the intent directly."
        assert decision.metadata == {"intent": "code"}

    def test_metadata_defaults_to_empty_dict(self) -> None:
        decision = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
        )

        assert decision.metadata == {}

    def test_all_fields_except_metadata_are_required(self) -> None:
        with pytest.raises(TypeError):
            Decision()  # type: ignore[call-arg]

    def test_construct_with_confirmation_required(self) -> None:
        decision = Decision(
            action=ASK_CONFIRMATION,
            confidence=0.9,
            requires_confirmation=True,
            explanation="explanation",
        )

        assert decision.requires_confirmation is True


class TestDecisionImmutability:
    """Tests for Decision immutability."""

    def test_decision_is_immutable(self) -> None:
        decision = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
        )

        with pytest.raises(FrozenInstanceError):
            decision.action = NOOP  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            decision.confidence = 0.5  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            decision.requires_confirmation = True  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            decision.explanation = "changed"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            decision.metadata = {"intent": "code"}  # type: ignore[misc]


class TestDecisionEquality:
    """Tests for Decision value equality."""

    def test_equal_decisions_are_equal(self) -> None:
        first = Decision(
            action=DEFER,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "memory"},
        )
        second = Decision(
            action=DEFER,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "memory"},
        )

        assert first == second

    def test_different_action_is_not_equal(self) -> None:
        first = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
        )
        second = Decision(
            action=REJECT,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
        )

        assert first != second

    def test_different_confidence_is_not_equal(self) -> None:
        first = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
        )
        second = Decision(
            action=EXECUTE,
            confidence=0.5,
            requires_confirmation=False,
            explanation="explanation",
        )

        assert first != second

    def test_different_metadata_is_not_equal(self) -> None:
        first = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "code"},
        )
        second = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "chat"},
        )

        assert first != second


class TestDecisionSerialization:
    """Tests for Decision serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        decision = Decision(
            action=ASK_CLARIFICATION,
            confidence=0.4,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "research"},
        )

        assert decision.to_dict() == {
            "action": ASK_CLARIFICATION,
            "confidence": 0.4,
            "requires_confirmation": False,
            "explanation": "explanation",
            "metadata": {"intent": "research"},
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Decision(
            action=ASK_CONFIRMATION,
            confidence=0.9,
            requires_confirmation=True,
            explanation="explanation",
            metadata={"intent": "workspace", "priority": "NORMAL"},
        )

        restored = Decision.from_dict(original.to_dict())

        assert restored == original
        assert restored.requires_confirmation is True

    def test_from_dict_without_metadata_defaults_empty(self) -> None:
        decision = Decision.from_dict(
            {
                "action": EXECUTE,
                "confidence": 0.9,
                "requires_confirmation": False,
                "explanation": "explanation",
            }
        )

        assert decision.metadata == {}

    def test_metadata_is_copied_on_serialization(self) -> None:
        decision = Decision(
            action=EXECUTE,
            confidence=0.9,
            requires_confirmation=False,
            explanation="explanation",
            metadata={"intent": "code"},
        )

        serialized = decision.to_dict()
        serialized["metadata"]["intent"] = "mutated"

        assert decision.metadata == {"intent": "code"}
        assert decision.to_dict()["metadata"] == {"intent": "code"}


class TestDecisionConstants:
    """Tests for decision action constants."""

    def test_valid_actions_contains_all_outcomes(self) -> None:
        assert VALID_ACTIONS == {
            EXECUTE,
            ASK_CONFIRMATION,
            ASK_CLARIFICATION,
            REJECT,
            DEFER,
            NOOP,
        }

    def test_valid_actions_are_unique_strings(self) -> None:
        assert len(VALID_ACTIONS) == 6
        assert all(isinstance(action, str) for action in VALID_ACTIONS)
