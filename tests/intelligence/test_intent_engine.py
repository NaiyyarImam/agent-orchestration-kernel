"""Unit tests for the IntentEngine."""

from __future__ import annotations

import pytest

from kernel.intelligence.intent import Intent
from kernel.intelligence.intent_engine import (
    FALLBACK_CONFIDENCE,
    FALLBACK_INTENT,
    INTENT_RULES,
    MATCHED_CONFIDENCE,
    IntentEngine,
)


@pytest.fixture
def engine() -> IntentEngine:
    """Provide an IntentEngine instance."""
    return IntentEngine()


class TestClassifyMatchedIntents:
    """Tests for classification of supported intents."""

    @pytest.mark.parametrize(
        "text",
        [
            "search latest AI news",
            "research quantum computing",
            "summarize this article",
        ],
    )
    def test_research_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "research"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "write python code",
            "implement a sorting function",
            "debug my script",
        ],
    )
    def test_code_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "code"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "remember this",
            "memorize my favorite color",
            "store this for later",
        ],
    )
    def test_remember_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "remember"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "recall what I stored",
            "recall my favorite color",
        ],
    )
    def test_recall_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "recall"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "search my memory for notes",
            "find my memory about the meeting",
            "look through my memory for the password",
        ],
    )
    def test_search_memory_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "search_memory"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "forget that memory",
            "delete memory about my password",
            "erase memory of the meeting",
        ],
    )
    def test_forget_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "forget"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "open my project",
            "list files in directory",
            "show the workspace folder",
        ],
    )
    def test_workspace_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "workspace"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "browse github",
            "visit example.com",
            "open url on the web",
        ],
    )
    def test_browser_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "browser"
        assert intent.confidence == MATCHED_CONFIDENCE

    @pytest.mark.parametrize(
        "text",
        [
            "use voice commands",
            "speech to text",
            "text to speech",
            "start listening",
            "transcribe this audio",
        ],
    )
    def test_voice_intent(self, engine: IntentEngine, text: str) -> None:
        intent = engine.classify(text)

        assert intent.name == "voice"
        assert intent.confidence == MATCHED_CONFIDENCE

    def test_returns_intent_instance(self, engine: IntentEngine) -> None:
        assert isinstance(engine.classify("search news"), Intent)


class TestClassifyFallback:
    """Tests for the chat fallback."""

    def test_unknown_input_falls_back_to_chat(self, engine: IntentEngine) -> None:
        intent = engine.classify("tell me a joke")

        assert intent.name == FALLBACK_INTENT
        assert intent.confidence == FALLBACK_CONFIDENCE

    def test_empty_string_falls_back_to_chat(self, engine: IntentEngine) -> None:
        intent = engine.classify("")

        assert intent.name == FALLBACK_INTENT
        assert intent.confidence == FALLBACK_CONFIDENCE

    def test_whitespace_only_falls_back_to_chat(self, engine: IntentEngine) -> None:
        intent = engine.classify("   \n\t  ")

        assert intent.name == FALLBACK_INTENT

    def test_punctuation_only_falls_back_to_chat(self, engine: IntentEngine) -> None:
        intent = engine.classify("!!?")

        assert intent.name == FALLBACK_INTENT


class TestClassifyCaseHandling:
    """Tests for case-insensitive classification."""

    def test_uppercase_request(self, engine: IntentEngine) -> None:
        intent = engine.classify("SEARCH LATEST AI NEWS")

        assert intent.name == "research"

    def test_mixed_case_request(self, engine: IntentEngine) -> None:
        intent = engine.classify("Write Python Code")

        assert intent.name == "code"

    def test_keyword_in_uppercase_sentence(self, engine: IntentEngine) -> None:
        intent = engine.classify("Please REMEMBER this for me")

        assert intent.name == "remember"


class TestClassifyParameters:
    """Tests for parameter extraction."""

    def test_parameters_include_original_text(self, engine: IntentEngine) -> None:
        intent = engine.classify("search latest AI news")

        assert intent.parameters == {"text": "search latest AI news"}

    def test_parameters_preserve_original_case(self, engine: IntentEngine) -> None:
        intent = engine.classify("Search Latest AI News")

        assert intent.parameters == {"text": "Search Latest AI News"}

    def test_fallback_parameters_include_text(self, engine: IntentEngine) -> None:
        intent = engine.classify("hello")

        assert intent.parameters == {"text": "hello"}


class TestClassifyConfidence:
    """Tests for confidence values."""

    def test_matched_confidence_constant(self) -> None:
        assert MATCHED_CONFIDENCE == 0.9

    def test_fallback_confidence_constant(self) -> None:
        assert FALLBACK_CONFIDENCE == 0.4

    def test_matched_confidence_higher_than_fallback(self) -> None:
        assert MATCHED_CONFIDENCE > FALLBACK_CONFIDENCE


class TestClassifyMultipleKeywords:
    """Tests for requests containing multiple keywords."""

    def test_first_rule_in_order_wins(self, engine: IntentEngine) -> None:
        intent = engine.classify("search for python code")

        assert intent.name == "research"

    def test_code_keyword_not_stolen_by_workspace(self, engine: IntentEngine) -> None:
        intent = engine.classify("write python code")

        assert intent.name == "code"

    def test_workspace_rule_checked_before_browser(self, engine: IntentEngine) -> None:
        intent = engine.classify("browse the web for files")

        assert intent.name == "workspace"


class TestClassifyStability:
    """Tests for deterministic, repeated classification."""

    def test_repeated_classification_is_stable(self, engine: IntentEngine) -> None:
        text = "search latest AI news"

        first = engine.classify(text)
        second = engine.classify(text)
        third = engine.classify(text)

        assert first == second == third
        assert first.name == "research"

    def test_leading_and_trailing_whitespace_ignored_for_classification(
        self, engine: IntentEngine
    ) -> None:
        padded = engine.classify("  search latest AI news  ")
        plain = engine.classify("search latest AI news")

        assert padded.name == plain.name == "research"
        assert padded.confidence == plain.confidence

    def test_returns_new_instance_each_call(self, engine: IntentEngine) -> None:
        text = "search news"
        assert engine.classify(text) is not engine.classify(text)


class TestSupports:
    """Tests for the supports method."""

    def test_supports_known_intents(self, engine: IntentEngine) -> None:
        for intent_name in INTENT_RULES:
            assert engine.supports(intent_name) is True

    def test_supports_unknown_intent(self, engine: IntentEngine) -> None:
        assert engine.supports("unknown") is False

    def test_supports_is_case_sensitive(self, engine: IntentEngine) -> None:
        assert engine.supports("Research") is False


class TestHealthCheck:
    """Tests for the engine health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self, engine: IntentEngine) -> None:
        assert await engine.health_check() is True
