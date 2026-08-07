"""Unit tests for the Reasoning model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.intelligence.reasoning import Reasoning


class TestReasoningConstruction:
    """Tests for Reasoning construction."""

    def test_construct_with_all_fields(self) -> None:
        reasoning = Reasoning(
            intent_name="code",
            capability="coding",
            explanation="Intent 'code' resolved to the 'coding' capability with HIGH priority.",
            priority="HIGH",
            requires_confirmation=False,
        )

        assert reasoning.intent_name == "code"
        assert reasoning.capability == "coding"
        assert reasoning.explanation == (
            "Intent 'code' resolved to the 'coding' capability with HIGH priority."
        )
        assert reasoning.priority == "HIGH"
        assert reasoning.requires_confirmation is False

    def test_all_fields_are_required(self) -> None:
        with pytest.raises(TypeError):
            Reasoning()  # type: ignore[call-arg]

    def test_construct_with_confirmation_required(self) -> None:
        reasoning = Reasoning(
            intent_name="workspace",
            capability="workspace",
            explanation="Intent 'workspace' resolved to the 'workspace' capability.",
            priority="NORMAL",
            requires_confirmation=True,
        )

        assert reasoning.requires_confirmation is True


class TestReasoningImmutability:
    """Tests for Reasoning immutability."""

    def test_reasoning_is_immutable(self) -> None:
        reasoning = Reasoning(
            intent_name="chat",
            capability="chat",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )

        with pytest.raises(FrozenInstanceError):
            reasoning.intent_name = "code"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            reasoning.capability = "coding"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            reasoning.explanation = "changed"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            reasoning.priority = "HIGH"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            reasoning.requires_confirmation = True  # type: ignore[misc]


class TestReasoningEquality:
    """Tests for Reasoning value equality."""

    def test_equal_reasoning_is_equal(self) -> None:
        first = Reasoning(
            intent_name="memory",
            capability="memory",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )
        second = Reasoning(
            intent_name="memory",
            capability="memory",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )

        assert first == second

    def test_different_capability_is_not_equal(self) -> None:
        first = Reasoning(
            intent_name="chat",
            capability="chat",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )
        second = Reasoning(
            intent_name="chat",
            capability="coding",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )

        assert first != second

    def test_different_priority_is_not_equal(self) -> None:
        first = Reasoning(
            intent_name="code",
            capability="coding",
            explanation="explanation",
            priority="HIGH",
            requires_confirmation=False,
        )
        second = Reasoning(
            intent_name="code",
            capability="coding",
            explanation="explanation",
            priority="LOW",
            requires_confirmation=False,
        )

        assert first != second

    def test_different_confirmation_is_not_equal(self) -> None:
        first = Reasoning(
            intent_name="workspace",
            capability="workspace",
            explanation="explanation",
            priority="NORMAL",
            requires_confirmation=False,
        )
        second = Reasoning(
            intent_name="workspace",
            capability="workspace",
            explanation="explanation",
            priority="NORMAL",
            requires_confirmation=True,
        )

        assert first != second


class TestReasoningSerialization:
    """Tests for Reasoning serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        reasoning = Reasoning(
            intent_name="browser",
            capability="browser",
            explanation="explanation",
            priority="NORMAL",
            requires_confirmation=False,
        )

        assert reasoning.to_dict() == {
            "intent_name": "browser",
            "capability": "browser",
            "explanation": "explanation",
            "priority": "NORMAL",
            "requires_confirmation": False,
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Reasoning(
            intent_name="workspace",
            capability="workspace",
            explanation="explanation",
            priority="NORMAL",
            requires_confirmation=True,
        )

        restored = Reasoning.from_dict(original.to_dict())

        assert restored == original
        assert restored.requires_confirmation is True
