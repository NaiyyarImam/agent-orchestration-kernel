"""Unit tests for the ReasoningEngine."""

from __future__ import annotations

import pytest

from kernel.intelligence.intent import Intent
from kernel.intelligence.reasoning import Reasoning
from kernel.intelligence.reasoning_engine import (
    FALLBACK_CAPABILITY,
    HIGH,
    LOW,
    NORMAL,
    REASONING_RULES,
    ReasoningEngine,
)


@pytest.fixture
def engine() -> ReasoningEngine:
    """Provide a ReasoningEngine instance."""
    return ReasoningEngine()


@pytest.fixture
def intent() -> Intent:
    """Provide a simple chat intent."""
    return Intent(name="chat", confidence=0.9)


class TestReasonAllIntents:
    """Tests for reasoning over every known intent mapping."""

    def test_rules_cover_all_documented_intents(self) -> None:
        expected = {
            "chat",
            "research",
            "code",
            "remember",
            "recall",
            "search_memory",
            "forget",
            "workspace",
            "browser",
            "voice",
        }

        assert set(REASONING_RULES) == expected

    @pytest.mark.parametrize(
        ("intent_name", "capability", "priority", "requires_confirmation"),
        [
            ("chat", "chat", LOW, False),
            ("research", "research", NORMAL, False),
            ("code", "coding", HIGH, False),
            ("remember", "remember", LOW, False),
            ("recall", "recall", LOW, False),
            ("search_memory", "search_memory", LOW, False),
            ("forget", "forget", LOW, False),
            ("workspace", "workspace", NORMAL, True),
            ("browser", "browser", NORMAL, False),
            ("voice", "voice", LOW, False),
        ],
    )
    def test_each_intent_maps_to_expected_reasoning(
        self,
        engine: ReasoningEngine,
        intent_name: str,
        capability: str,
        priority: str,
        requires_confirmation: bool,
    ) -> None:
        reasoning = engine.reason(Intent(name=intent_name, confidence=0.9))

        assert reasoning.intent_name == intent_name
        assert reasoning.capability == capability
        assert reasoning.priority == priority
        assert reasoning.requires_confirmation is requires_confirmation

    def test_reasoning_is_a_reasoning_instance(self, engine: ReasoningEngine) -> None:
        reasoning = engine.reason(Intent(name="chat", confidence=0.9))

        assert isinstance(reasoning, Reasoning)

    def test_confidence_and_parameters_do_not_affect_reasoning(
        self, engine: ReasoningEngine
    ) -> None:
        plain = engine.reason(Intent(name="code", confidence=0.4))
        confident = engine.reason(
            Intent(name="code", confidence=0.9, parameters={"text": "write code"})
        )

        assert plain == confident


class TestReasonPriorityAssignment:
    """Tests for priority assignment."""

    def test_code_is_high_priority(self, engine: ReasoningEngine) -> None:
        assert engine.reason(Intent(name="code", confidence=0.9)).priority == HIGH

    def test_research_is_normal_priority(self, engine: ReasoningEngine) -> None:
        assert engine.reason(Intent(name="research", confidence=0.9)).priority == NORMAL

    def test_browser_is_normal_priority(self, engine: ReasoningEngine) -> None:
        assert engine.reason(Intent(name="browser", confidence=0.9)).priority == NORMAL

    def test_workspace_is_normal_priority(self, engine: ReasoningEngine) -> None:
        assert (
            engine.reason(Intent(name="workspace", confidence=0.9)).priority == NORMAL
        )

    def test_memory_operations_are_low_priority(self, engine: ReasoningEngine) -> None:
        for intent_name in ("remember", "recall", "search_memory", "forget"):
            assert (
                engine.reason(Intent(name=intent_name, confidence=0.9)).priority == LOW
            )

    def test_chat_is_low_priority(self, engine: ReasoningEngine) -> None:
        assert engine.reason(Intent(name="chat", confidence=0.9)).priority == LOW


class TestReasonConfirmationAssignment:
    """Tests for confirmation assignment."""

    def test_only_workspace_requires_confirmation(
        self, engine: ReasoningEngine
    ) -> None:
        for intent_name in REASONING_RULES:
            reasoning = engine.reason(Intent(name=intent_name, confidence=0.9))

            assert reasoning.requires_confirmation is (intent_name == "workspace")


class TestReasonExplanation:
    """Tests for explanation generation."""

    def test_explanation_mentions_intent_and_capability(
        self, engine: ReasoningEngine
    ) -> None:
        reasoning = engine.reason(Intent(name="code", confidence=0.9))

        assert "code" in reasoning.explanation
        assert "coding" in reasoning.explanation

    def test_explanation_is_human_readable(self, engine: ReasoningEngine) -> None:
        reasoning = engine.reason(Intent(name="research", confidence=0.9))

        assert reasoning.explanation == (
            "Intent 'research' resolved to the 'research' capability with NORMAL priority."
        )

    def test_explanation_is_not_empty_for_every_intent(
        self, engine: ReasoningEngine
    ) -> None:
        for intent_name in REASONING_RULES:
            reasoning = engine.reason(Intent(name=intent_name, confidence=0.9))

            assert reasoning.explanation
            assert reasoning.explanation.islower() or any(
                marker in reasoning.explanation for marker in ("HIGH", "NORMAL", "LOW")
            )


class TestReasonFallback:
    """Tests for unknown intent fallback."""

    def test_unknown_intent_falls_back_to_chat(self, engine: ReasoningEngine) -> None:
        reasoning = engine.reason(Intent(name="unknown", confidence=0.9))

        assert reasoning.capability == FALLBACK_CAPABILITY
        assert reasoning.priority == LOW
        assert reasoning.requires_confirmation is False

    def test_fallback_preserves_original_intent_name(
        self, engine: ReasoningEngine
    ) -> None:
        reasoning = engine.reason(Intent(name="mystery", confidence=0.5))

        assert reasoning.intent_name == "mystery"

    def test_fallback_explanation_matches_chat_capability(
        self, engine: ReasoningEngine
    ) -> None:
        reasoning = engine.reason(Intent(name="mystery", confidence=0.5))

        assert "chat" in reasoning.explanation


class TestReasonInvalidInputs:
    """Tests for invalid input handling."""

    def test_none_intent_raises_value_error(self, engine: ReasoningEngine) -> None:
        with pytest.raises(ValueError, match="intent is required"):
            engine.reason(None)  # type: ignore[arg-type]

    def test_empty_intent_name_falls_back_to_chat(
        self, engine: ReasoningEngine
    ) -> None:
        reasoning = engine.reason(Intent(name="", confidence=0.9))

        assert reasoning.capability == FALLBACK_CAPABILITY
        assert reasoning.priority == LOW
        assert reasoning.requires_confirmation is False


class TestReasonDeterminism:
    """Tests for deterministic repeated reasoning."""

    def test_repeated_reasoning_is_stable(self, engine: ReasoningEngine) -> None:
        intent = Intent(name="code", confidence=0.9)

        first = engine.reason(intent)
        second = engine.reason(intent)
        third = engine.reason(intent)

        assert first == second == third
        assert first.capability == "coding"
        assert first.priority == HIGH

    def test_repeated_fallback_is_stable(self, engine: ReasoningEngine) -> None:
        intent = Intent(name="unknown", confidence=0.4)

        assert engine.reason(intent) == engine.reason(intent)

    def test_returns_new_instance_each_call(self, engine: ReasoningEngine) -> None:
        intent = Intent(name="chat", confidence=0.9)

        assert engine.reason(intent) is not engine.reason(intent)


class TestSupports:
    """Tests for the supports method."""

    def test_supports_known_intents(self, engine: ReasoningEngine) -> None:
        for intent_name in REASONING_RULES:
            assert engine.supports(intent_name) is True

    def test_supports_unknown_intent(self, engine: ReasoningEngine) -> None:
        assert engine.supports("unknown") is False

    def test_supports_is_case_sensitive(self, engine: ReasoningEngine) -> None:
        assert engine.supports("Code") is False
