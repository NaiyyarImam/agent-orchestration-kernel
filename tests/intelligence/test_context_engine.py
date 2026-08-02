"""Unit tests for the ContextEngine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kernel.intelligence.context import Context
from kernel.intelligence.context_engine import (
    DICT_FIELDS,
    SCALAR_FIELDS,
    SUPPORTED_CAPABILITIES,
    ContextEngine,
)

FIXED_TIMESTAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


@pytest.fixture
def engine() -> ContextEngine:
    """Provide a ContextEngine instance."""
    return ContextEngine()


@pytest.fixture
def base_context() -> Context:
    """Provide a fully populated Context."""
    return Context(
        user_input="hello",
        conversation_id="conv-1",
        session_id="session-1",
        timestamp=FIXED_TIMESTAMP,
        working_memory={"a": 1, "nested": {"x": 1}},
        environment={"os": "darwin"},
        metadata={"source": "cli"},
    )


class TestConstants:
    """Tests for engine constants."""

    def test_scalar_fields_are_defined(self) -> None:
        assert SCALAR_FIELDS == (
            "user_input",
            "conversation_id",
            "session_id",
            "timestamp",
        )

    def test_dict_fields_are_defined(self) -> None:
        assert DICT_FIELDS == ("working_memory", "environment", "metadata")

    def test_field_groups_cover_all_context_fields(self) -> None:
        all_fields = set(SCALAR_FIELDS + DICT_FIELDS)

        assert all_fields == {
            "user_input",
            "conversation_id",
            "session_id",
            "timestamp",
            "working_memory",
            "environment",
            "metadata",
        }


class TestBuild:
    """Tests for context construction."""

    def test_build_with_all_fields(self, engine: ContextEngine) -> None:
        context = engine.build(
            user_input="search news",
            conversation_id="conv-1",
            session_id="session-1",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"a": 1},
            environment={"os": "darwin"},
            metadata={"source": "cli"},
        )

        assert isinstance(context, Context)
        assert context.user_input == "search news"
        assert context.conversation_id == "conv-1"
        assert context.session_id == "session-1"
        assert context.timestamp == FIXED_TIMESTAMP
        assert context.working_memory == {"a": 1}
        assert context.environment == {"os": "darwin"}
        assert context.metadata == {"source": "cli"}

    def test_build_with_defaults(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello")

        assert context.conversation_id is None
        assert context.session_id is None
        assert isinstance(context.timestamp, datetime)
        assert context.timestamp.tzinfo is timezone.utc
        assert context.working_memory == {}
        assert context.environment == {}
        assert context.metadata == {}

    def test_build_uses_supplied_timestamp(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello", timestamp=FIXED_TIMESTAMP)

        assert context.timestamp == FIXED_TIMESTAMP

    def test_build_with_non_string_input_raises_value_error(
        self, engine: ContextEngine
    ) -> None:
        with pytest.raises(ValueError, match="user_input must be a string"):
            engine.build(user_input=123)  # type: ignore[arg-type]

    def test_build_without_user_input_raises_type_error(
        self, engine: ContextEngine
    ) -> None:
        with pytest.raises(TypeError):
            engine.build()  # type: ignore[call-arg]

    def test_build_deep_copies_input_dicts(self, engine: ContextEngine) -> None:
        working_memory = {"nested": {"a": 1}}
        context = engine.build(user_input="hello", working_memory=working_memory)

        working_memory["nested"]["a"] = "mutated"

        assert context.working_memory == {"nested": {"a": 1}}


class TestUpdate:
    """Tests for context updates."""

    def test_update_replaces_scalar_fields(self, engine: ContextEngine) -> None:
        updated = engine.update(
            engine.build(user_input="hello", conversation_id="conv-1"),
            user_input="world",
            conversation_id="conv-2",
        )

        assert updated.user_input == "world"
        assert updated.conversation_id == "conv-2"

    def test_update_sets_scalar_field_to_none(self, engine: ContextEngine) -> None:
        updated = engine.update(
            engine.build(user_input="hello", conversation_id="conv-1"),
            conversation_id=None,
        )

        assert updated.conversation_id is None

    def test_update_merges_working_memory(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello", working_memory={"a": 1})

        updated = engine.update(context, working_memory={"b": 2})

        assert updated.working_memory == {"a": 1, "b": 2}
        assert context.working_memory == {"a": 1}

    def test_update_merges_environment_and_metadata(
        self, engine: ContextEngine
    ) -> None:
        context = engine.build(
            user_input="hello", environment={"os": "darwin"}, metadata={"source": "cli"}
        )

        updated = engine.update(
            context, environment={"arch": "arm64"}, metadata={"v": 2}
        )

        assert updated.environment == {"os": "darwin", "arch": "arm64"}
        assert updated.metadata == {"source": "cli", "v": 2}

    def test_update_merges_nested_dicts(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello", working_memory={"nested": {"x": 1}})

        updated = engine.update(context, working_memory={"nested": {"y": 2}})

        assert updated.working_memory == {"nested": {"x": 1, "y": 2}}

    def test_update_replaces_timestamp(self, engine: ContextEngine) -> None:
        updated = engine.update(
            engine.build(user_input="hello"), timestamp=FIXED_TIMESTAMP
        )

        assert updated.timestamp == FIXED_TIMESTAMP

    def test_update_without_changes_returns_same_context(
        self, engine: ContextEngine
    ) -> None:
        context = engine.build(user_input="hello")

        assert engine.update(context) is context

    def test_update_with_none_dicts_is_ignored(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello", working_memory={"a": 1})

        updated = engine.update(context, working_memory=None)  # type: ignore[arg-type]

        assert updated.working_memory == {"a": 1}

    def test_update_unknown_field_raises_value_error(
        self, engine: ContextEngine
    ) -> None:
        with pytest.raises(ValueError, match="Unknown context field 'bogus'"):
            engine.update(engine.build(user_input="hello"), bogus=1)  # type: ignore[call-arg]

    def test_update_with_none_context_raises_value_error(
        self, engine: ContextEngine
    ) -> None:
        with pytest.raises(ValueError, match="context is required"):
            engine.update(None, user_input="world")  # type: ignore[arg-type]


class TestMerge:
    """Tests for context merging."""

    def test_merge_combines_both_contexts(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(user_input="world", working_memory={"b": 2})

        merged = engine.merge(base_context, other)

        assert isinstance(merged, Context)
        assert merged.user_input == "world"
        assert merged.conversation_id == "conv-1"
        assert merged.session_id == "session-1"
        assert merged.timestamp == other.timestamp
        assert merged.working_memory == {"a": 1, "nested": {"x": 1}, "b": 2}
        assert merged.environment == {"os": "darwin"}
        assert merged.metadata == {"source": "cli"}

    def test_merge_does_not_mutate_inputs(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(user_input="world", working_memory={"b": 2})

        engine.merge(base_context, other)

        assert base_context.working_memory == {"a": 1, "nested": {"x": 1}}
        assert other.working_memory == {"b": 2}

    def test_merge_second_wins_conflicts(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(
            user_input="world",
            conversation_id="conv-2",
            session_id="session-2",
            working_memory={"a": 9},
        )

        merged = engine.merge(base_context, other)

        assert merged.user_input == "world"
        assert merged.conversation_id == "conv-2"
        assert merged.session_id == "session-2"
        assert merged.working_memory == {"a": 9, "nested": {"x": 1}}

    def test_merge_nested_dictionaries(self, engine: ContextEngine) -> None:
        first = Context(
            user_input="a",
            working_memory={"level": {"inner": {"deep": 1, "keep": 1}}},
        )
        second = Context(
            user_input="b",
            working_memory={"level": {"inner": {"deep": 2, "more": 3}}},
        )

        merged = engine.merge(first, second)

        assert merged.working_memory == {
            "level": {"inner": {"deep": 2, "keep": 1, "more": 3}}
        }

    def test_merge_non_dict_value_overrides_nested_dict(
        self, engine: ContextEngine
    ) -> None:
        first = Context(user_input="a", working_memory={"key": {"x": 1}})
        second = Context(user_input="b", working_memory={"key": "scalar"})

        merged = engine.merge(first, second)

        assert merged.working_memory == {"key": "scalar"}

    def test_merge_merges_all_dict_fields(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(
            user_input="world",
            working_memory={"b": 2},
            environment={"arch": "arm64"},
            metadata={"v": 2},
        )

        merged = engine.merge(base_context, other)

        assert merged.environment == {"os": "darwin", "arch": "arm64"}
        assert merged.metadata == {"source": "cli", "v": 2}

    def test_merge_with_none_inputs_raises_value_error(
        self, engine: ContextEngine
    ) -> None:
        context = engine.build(user_input="hello")

        with pytest.raises(ValueError, match="contexts are required"):
            engine.merge(None, context)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="contexts are required"):
            engine.merge(context, None)  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="contexts are required"):
            engine.merge(None, None)  # type: ignore[arg-type]


class TestMergePrecedence:
    """Tests for merge precedence rules."""

    def test_second_context_overrides_conflicting_values(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(
            user_input="world",
            conversation_id="conv-2",
            timestamp=FIXED_TIMESTAMP,
            working_memory={"a": 99},
        )

        merged = engine.merge(base_context, other)

        assert merged.user_input == "world"
        assert merged.conversation_id == "conv-2"
        assert merged.timestamp == FIXED_TIMESTAMP
        assert merged.working_memory["a"] == 99

    def test_second_none_identifiers_keep_first(
        self, engine: ContextEngine, base_context: Context
    ) -> None:
        other = Context(user_input="world")

        merged = engine.merge(base_context, other)

        assert merged.conversation_id == "conv-1"
        assert merged.session_id == "session-1"

    def test_merge_is_deterministic(self, engine: ContextEngine) -> None:
        first = Context(user_input="a", working_memory={"x": 1})
        second = Context(user_input="b", working_memory={"x": 2, "y": 1})

        assert engine.merge(first, second) == engine.merge(first, second)


class TestExplain:
    """Tests for explanation generation."""

    def test_explain_describes_context(self, engine: ContextEngine) -> None:
        context = Context(
            user_input="search news",
            conversation_id="conv-1",
            session_id="session-1",
            working_memory={"a": 1},
            environment={"os": "darwin"},
            metadata={"source": "cli"},
        )

        explanation = engine.explain(context)

        assert "search news" in explanation
        assert "conv-1" in explanation
        assert "session-1" in explanation
        assert "1 working memory" in explanation
        assert "1 environment" in explanation
        assert "1 metadata" in explanation

    def test_explain_without_identifiers_uses_unknown(
        self, engine: ContextEngine
    ) -> None:
        context = Context(user_input="hello")

        explanation = engine.explain(context)

        assert "conversation 'unknown'" in explanation
        assert "session 'unknown'" in explanation

    def test_explain_is_deterministic(self, engine: ContextEngine) -> None:
        context = Context(user_input="hello", conversation_id="conv-1")

        assert engine.explain(context) == engine.explain(context)

    def test_explain_with_none_context_raises_value_error(
        self, engine: ContextEngine
    ) -> None:
        with pytest.raises(ValueError, match="context is required"):
            engine.explain(None)  # type: ignore[arg-type]


class TestSupports:
    """Tests for the supports helper."""

    def test_supports_context_capability(self, engine: ContextEngine) -> None:
        for capability in SUPPORTED_CAPABILITIES:
            assert engine.supports(capability) is True

    def test_supports_unsupported_capability(self, engine: ContextEngine) -> None:
        assert engine.supports("research") is False

    def test_supports_is_case_sensitive(self, engine: ContextEngine) -> None:
        assert engine.supports("Context") is False


class TestHealthCheck:
    """Tests for the engine health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, engine: ContextEngine) -> None:
        assert await engine.health_check() == {"healthy": True}


class TestDeterminism:
    """Tests for deterministic engine behavior."""

    def test_build_is_deterministic(self, engine: ContextEngine) -> None:
        kwargs = {
            "user_input": "hello",
            "conversation_id": "conv-1",
            "timestamp": FIXED_TIMESTAMP,
            "working_memory": {"a": 1},
        }

        assert engine.build(**kwargs) == engine.build(**kwargs)

    def test_update_is_deterministic(self, engine: ContextEngine) -> None:
        context = engine.build(user_input="hello", working_memory={"a": 1})

        assert engine.update(context, working_memory={"b": 2}) == engine.update(
            context, working_memory={"b": 2}
        )

    def test_merge_returns_new_instance(self, engine: ContextEngine) -> None:
        first = Context(user_input="a")
        second = Context(user_input="b")

        assert engine.merge(first, second) is not first
        assert engine.merge(first, second) is not second
