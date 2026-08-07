"""Unit tests for the Context model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from kernel.intelligence.context import Context

FIXED_TIMESTAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


class TestContextConstruction:
    """Tests for Context construction."""

    def test_construct_with_all_fields(self) -> None:
        context = Context(
            user_input="search latest AI news",
            conversation_id="conv-1",
            session_id="session-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"preferences": {"tone": "formal"}},
            environment={"os": "darwin"},
            metadata={"source": "cli"},
        )

        assert context.user_input == "search latest AI news"
        assert context.conversation_id == "conv-1"
        assert context.session_id == "session-1"
        assert context.timestamp == FIXED_TIMESTAMP
        assert context.working_memory == {"preferences": {"tone": "formal"}}
        assert context.environment == {"os": "darwin"}
        assert context.metadata == {"source": "cli"}

    def test_user_input_is_required(self) -> None:
        with pytest.raises(TypeError):
            Context()  # type: ignore[call-arg]

    def test_defaults_are_applied(self) -> None:
        context = Context(user_input="hello")

        assert context.conversation_id is None
        assert context.session_id is None
        assert isinstance(context.timestamp, datetime)
        assert context.timestamp.tzinfo is timezone.utc
        assert context.working_memory == {}
        assert context.environment == {}
        assert context.metadata == {}

    def test_dict_fields_default_to_empty_dicts(self) -> None:
        first = Context(user_input="a")
        second = Context(user_input="b")

        assert first.working_memory == {}
        assert second.working_memory == {}


class TestContextImmutability:
    """Tests for Context immutability."""

    def test_context_is_immutable(self) -> None:
        context = Context(user_input="hello")

        with pytest.raises(FrozenInstanceError):
            context.user_input = "world"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.conversation_id = "conv-1"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.session_id = "session-1"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.timestamp = FIXED_TIMESTAMP  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.working_memory = {"a": 1}  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.environment = {"a": 1}  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            context.metadata = {"a": 1}  # type: ignore[misc]


class TestContextEquality:
    """Tests for Context value equality."""

    def test_equal_contexts_are_equal(self) -> None:
        first = Context(
            user_input="hello",
            conversation_id="conv-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"a": 1},
        )
        second = Context(
            user_input="hello",
            conversation_id="conv-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"a": 1},
        )

        assert first == second

    def test_different_user_input_is_not_equal(self) -> None:
        assert Context(user_input="a") != Context(user_input="b")

    def test_different_conversation_id_is_not_equal(self) -> None:
        first = Context(user_input="a", conversation_id="conv-1")
        second = Context(user_input="a", conversation_id="conv-2")

        assert first != second

    def test_different_timestamp_is_not_equal(self) -> None:
        first = Context(user_input="a", timestamp=FIXED_TIMESTAMP)
        second = Context(
            user_input="a", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )

        assert first != second

    def test_different_working_memory_is_not_equal(self) -> None:
        first = Context(user_input="a", working_memory={"a": 1})
        second = Context(user_input="a", working_memory={"a": 2})

        assert first != second


class TestContextSerialization:
    """Tests for Context serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        context = Context(
            user_input="hello",
            conversation_id="conv-1",
            session_id="session-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"nested": {"a": 1}},
            environment={"os": "darwin"},
            metadata={"source": "cli"},
        )

        assert context.to_dict() == {
            "user_input": "hello",
            "conversation_id": "conv-1",
            "session_id": "session-1",
            "timestamp": "2026-01-02T03:04:05+00:00",
            "working_memory": {"nested": {"a": 1}},
            "environment": {"os": "darwin"},
            "metadata": {"source": "cli"},
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Context(
            user_input="hello",
            conversation_id="conv-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"nested": {"a": 1}},
        )

        restored = Context.from_dict(original.to_dict())

        assert restored == original
        assert restored.timestamp == FIXED_TIMESTAMP

    def test_from_dict_without_optional_keys_defaults(self) -> None:
        context = Context.from_dict(
            {
                "user_input": "hello",
                "timestamp": "2026-01-02T03:04:05+00:00",
            }
        )

        assert context.conversation_id is None
        assert context.session_id is None
        assert context.working_memory == {}
        assert context.environment == {}
        assert context.metadata == {}

    def test_timestamp_is_serialized_as_iso_string(self) -> None:
        context = Context(user_input="hello", timestamp=FIXED_TIMESTAMP)

        assert context.to_dict()["timestamp"] == "2026-01-02T03:04:05+00:00"

    def test_serialization_deep_copies_nested_dicts(self) -> None:
        context = Context(
            user_input="hello",
            working_memory={"nested": {"a": 1}},
        )

        serialized = context.to_dict()
        serialized["working_memory"]["nested"]["a"] = "mutated"

        assert context.working_memory == {"nested": {"a": 1}}
        assert context.to_dict()["working_memory"] == {"nested": {"a": 1}}
