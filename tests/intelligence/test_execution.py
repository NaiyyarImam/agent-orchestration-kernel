"""Unit tests for the Execution model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.intelligence.execution import (
    CANCELLED,
    COMPLETED,
    DEFAULT_STATUS,
    EXECUTION_STATUSES,
    FAILED,
    PENDING,
    RUNNING,
    Execution,
)


class TestExecutionConstruction:
    """Tests for Execution construction."""

    def test_construct_with_all_fields(self) -> None:
        execution = Execution(
            execution_id="exec-123",
            plan_id="plan-123",
            action="execute",
            status=COMPLETED,
            success=True,
            confidence=0.9,
            metadata={"plan_action": "execute"},
        )

        assert execution.execution_id == "exec-123"
        assert execution.plan_id == "plan-123"
        assert execution.action == "execute"
        assert execution.status == COMPLETED
        assert execution.success is True
        assert execution.confidence == 0.9
        assert execution.metadata == {"plan_action": "execute"}

    def test_identifier_and_action_fields_are_required(self) -> None:
        with pytest.raises(TypeError):
            Execution()  # type: ignore[call-arg]

    def test_defaults_are_applied(self) -> None:
        execution = Execution(execution_id="exec-1", plan_id="plan-1", action="execute")

        assert execution.status == DEFAULT_STATUS == PENDING
        assert execution.success is False
        assert execution.confidence == 0.0
        assert execution.metadata == {}


class TestExecutionImmutability:
    """Tests for Execution immutability."""

    def test_execution_is_immutable(self) -> None:
        execution = Execution(execution_id="exec-1", plan_id="plan-1", action="execute")

        with pytest.raises(FrozenInstanceError):
            execution.execution_id = "exec-2"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.plan_id = "plan-2"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.action = "deny"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.status = COMPLETED  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.success = True  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.confidence = 0.5  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            execution.metadata = {"a": 1}  # type: ignore[misc]


class TestExecutionEquality:
    """Tests for Execution value equality."""

    def test_equal_executions_are_equal(self) -> None:
        first = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="execute",
            status=COMPLETED,
            success=True,
            confidence=0.9,
        )
        second = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="execute",
            status=COMPLETED,
            success=True,
            confidence=0.9,
        )

        assert first == second

    def test_different_execution_id_is_not_equal(self) -> None:
        assert Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute"
        ) != Execution(execution_id="exec-2", plan_id="plan-1", action="execute")

    def test_different_status_is_not_equal(self) -> None:
        first = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", status=PENDING
        )
        second = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", status=RUNNING
        )

        assert first != second

    def test_different_success_is_not_equal(self) -> None:
        first = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", success=False
        )
        second = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", success=True
        )

        assert first != second

    def test_different_confidence_is_not_equal(self) -> None:
        first = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", confidence=0.5
        )
        second = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", confidence=0.9
        )

        assert first != second

    def test_different_metadata_is_not_equal(self) -> None:
        first = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="execute",
            metadata={"a": 1},
        )
        second = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="execute",
            metadata={"a": 2},
        )

        assert first != second


class TestExecutionSerialization:
    """Tests for Execution serialization."""

    def test_to_dict_includes_all_fields(self) -> None:
        execution = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="defer",
            status=FAILED,
            success=False,
            confidence=0.4,
            metadata={"plan_action": "defer"},
        )

        assert execution.to_dict() == {
            "execution_id": "exec-1",
            "plan_id": "plan-1",
            "action": "defer",
            "status": FAILED,
            "success": False,
            "confidence": 0.4,
            "metadata": {"plan_action": "defer"},
        }

    def test_from_dict_roundtrip(self) -> None:
        original = Execution(
            execution_id="exec-1",
            plan_id="plan-1",
            action="execute",
            status=CANCELLED,
            success=False,
            confidence=0.8,
            metadata={"goal": "goal"},
        )

        restored = Execution.from_dict(original.to_dict())

        assert restored == original

    def test_from_dict_without_optional_keys_defaults(self) -> None:
        execution = Execution.from_dict(
            {
                "execution_id": "exec-1",
                "plan_id": "plan-1",
                "action": "execute",
            }
        )

        assert execution.status == PENDING
        assert execution.success is False
        assert execution.confidence == 0.0
        assert execution.metadata == {}


class TestExecutionConstants:
    """Tests for execution status constants."""

    def test_statuses_contains_all_outcomes(self) -> None:
        assert EXECUTION_STATUSES == {PENDING, RUNNING, COMPLETED, FAILED, CANCELLED}

    def test_statuses_are_unique_strings(self) -> None:
        assert len(EXECUTION_STATUSES) == 5
        assert all(isinstance(status, str) for status in EXECUTION_STATUSES)
