"""Unit tests for the Intent model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.intelligence.intent import Intent


class TestIntentConstruction:
    """Tests for Intent construction."""

    def test_construct_with_all_fields(self) -> None:
        intent = Intent(
            name="research",
            confidence=0.9,
            parameters={"query": "AI news"},
        )

        assert intent.name == "research"
        assert intent.confidence == 0.9
        assert intent.parameters == {"query": "AI news"}

    def test_parameters_default_to_empty_dict(self) -> None:
        intent = Intent(name="chat", confidence=0.4)

        assert intent.parameters == {}

    def test_name_and_confidence_are_required(self) -> None:
        with pytest.raises(TypeError):
            Intent()  # type: ignore[call-arg]

    def test_intent_is_immutable(self) -> None:
        intent = Intent(name="code", confidence=0.9)

        with pytest.raises(FrozenInstanceError):
            intent.name = "research"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            intent.confidence = 0.5  # type: ignore[misc]


class TestIntentEquality:
    """Tests for Intent value equality."""

    def test_equal_intents_are_equal(self) -> None:
        first = Intent(name="memory", confidence=0.9)
        second = Intent(name="memory", confidence=0.9)

        assert first == second

    def test_different_parameters_are_not_equal(self) -> None:
        first = Intent(name="memory", confidence=0.9, parameters={"a": 1})
        second = Intent(name="memory", confidence=0.9, parameters={"a": 2})

        assert first != second

    def test_different_confidence_is_not_equal(self) -> None:
        assert Intent(name="chat", confidence=0.4) != Intent(name="chat", confidence=0.9)


class TestIntentSerialization:
    """Tests for Intent serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        intent = Intent(
            name="browser",
            confidence=0.9,
            parameters={"url": "github.com"},
        )

        data = intent.to_dict()

        assert data == {
            "name": "browser",
            "confidence": 0.9,
            "parameters": {"url": "github.com"},
        }

    def test_to_dict_with_empty_parameters(self) -> None:
        intent = Intent(name="chat", confidence=0.4)

        assert intent.to_dict() == {
            "name": "chat",
            "confidence": 0.4,
            "parameters": {},
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Intent(
            name="workspace",
            confidence=0.9,
            parameters={"path": "/tmp"},
        )

        restored = Intent.from_dict(original.to_dict())

        assert restored == original
        assert restored.parameters == {"path": "/tmp"}

    def test_from_dict_without_parameters_defaults_empty(self) -> None:
        intent = Intent.from_dict({"name": "research", "confidence": 0.9})

        assert intent.parameters == {}

    def test_parameters_are_copied_on_serialization(self) -> None:
        parameters = {"query": "news"}
        intent = Intent(name="research", confidence=0.9, parameters=parameters)

        serialized = intent.to_dict()

        serialized["parameters"]["query"] = "mutated"

        assert intent.parameters == {"query": "news"}
        assert intent.to_dict()["parameters"] == {"query": "news"}
