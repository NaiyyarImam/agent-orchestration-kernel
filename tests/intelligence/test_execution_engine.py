"""Unit tests for the ExecutionEngine."""

from __future__ import annotations

import pytest

from kernel.intelligence.execution import (
    CANCELLED,
    COMPLETED,
    EXECUTION_STATUSES,
    FAILED,
    PENDING,
    RUNNING,
    Execution,
)
from kernel.intelligence.execution_engine import ExecutionEngine
from kernel.intelligence.plan import EXECUTE, Plan


def make_plan(
    goal: str = "Resolve intent 'chat' with action 'execute'",
    action: str = EXECUTE,
    priority: int = 1,
    confidence: float = 0.9,
) -> Plan:
    """Build a Plan for execution tests."""
    return Plan(
        goal=goal,
        action=action,
        priority=priority,
        requires_confirmation=False,
        confidence=confidence,
        steps=("Validate decision", "Execute task"),
        metadata={"decision_action": "execute", "intent": "chat"},
    )


@pytest.fixture
def engine() -> ExecutionEngine:
    """Provide an ExecutionEngine instance."""
    return ExecutionEngine()


class TestExecuteSuccess:
    """Tests for successful execution."""

    def test_valid_plan_completes(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        assert execution.status == COMPLETED
        assert execution.success is True

    def test_action_is_propagated(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan(action="defer"))

        assert execution.action == "defer"

    def test_returns_execution_instance(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        assert isinstance(execution, Execution)


class TestExecuteFailure:
    """Tests for failed execution."""

    def test_invalid_plan_fails(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan(goal=""))

        assert execution.status == FAILED
        assert execution.success is False

    def test_none_plan_fails(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(None)  # type: ignore[arg-type]

        assert execution.status == FAILED
        assert execution.success is False
        assert execution.action == "unknown"
        assert execution.confidence == 0.0

    def test_failed_execution_is_never_successful(
        self, engine: ExecutionEngine
    ) -> None:
        for plan in [make_plan(goal=""), make_plan(action="")]:
            execution = engine.execute(plan)

            assert execution.status == FAILED
            assert execution.success is False


class TestExecuteConfidence:
    """Tests for confidence propagation."""

    def test_confidence_is_copied_from_plan(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan(confidence=0.5))

        assert execution.confidence == 0.5

    def test_boundary_confidences_are_preserved(self, engine: ExecutionEngine) -> None:
        assert engine.execute(make_plan(confidence=0.0)).confidence == 0.0
        assert engine.execute(make_plan(confidence=1.0)).confidence == 1.0


class TestExecuteMetadata:
    """Tests for execution metadata."""

    def test_metadata_includes_plan_action_and_goal(
        self, engine: ExecutionEngine
    ) -> None:
        plan = make_plan(goal="Resolve intent 'code' with action 'execute'")
        execution = engine.execute(plan)

        assert execution.metadata == {
            "plan_action": EXECUTE,
            "goal": "Resolve intent 'code' with action 'execute'",
        }


class TestDeterministicIds:
    """Tests for deterministic identifier generation."""

    def test_same_plan_produces_same_ids(self, engine: ExecutionEngine) -> None:
        plan = make_plan()

        first = engine.execute(plan)
        second = engine.execute(plan)

        assert first.execution_id == second.execution_id
        assert first.plan_id == second.plan_id

    def test_different_plans_produce_different_ids(
        self, engine: ExecutionEngine
    ) -> None:
        first = engine.execute(make_plan(goal="goal a"))
        second = engine.execute(make_plan(goal="goal b"))

        assert first.execution_id != second.execution_id

    def test_ids_are_prefixed(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        assert execution.execution_id.startswith("exec-")
        assert execution.plan_id.startswith("plan-")

    def test_none_plan_has_stable_unknown_id(self, engine: ExecutionEngine) -> None:
        first = engine.execute(None)  # type: ignore[arg-type]
        second = engine.execute(None)  # type: ignore[arg-type]

        assert first.execution_id == second.execution_id == "exec-unknown"
        assert first.plan_id == second.plan_id == "plan-unknown"

    def test_execution_is_fully_deterministic(self, engine: ExecutionEngine) -> None:
        plan = make_plan()

        assert engine.execute(plan) == engine.execute(plan)


class TestValidate:
    """Tests for execution validation."""

    def test_valid_execution_is_accepted(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        assert engine.validate(execution) is True

    def test_none_execution_is_rejected(self, engine: ExecutionEngine) -> None:
        assert engine.validate(None) is False  # type: ignore[arg-type]

    def test_empty_execution_id_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(execution_id="", plan_id="plan-1", action="execute")

        assert engine.validate(execution) is False

    def test_empty_plan_id_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(execution_id="exec-1", plan_id="", action="execute")

        assert engine.validate(execution) is False

    def test_empty_action_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(execution_id="exec-1", plan_id="plan-1", action="")

        assert engine.validate(execution) is False

    def test_unknown_status_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", status="BOGUS"
        )

        assert engine.validate(execution) is False

    @pytest.mark.parametrize("status", [PENDING, RUNNING, COMPLETED, FAILED, CANCELLED])
    def test_every_known_status_is_accepted(
        self, engine: ExecutionEngine, status: str
    ) -> None:
        execution = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", status=status
        )

        assert engine.validate(execution) is True

    def test_negative_confidence_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", confidence=-0.1
        )

        assert engine.validate(execution) is False

    def test_confidence_above_one_is_rejected(self, engine: ExecutionEngine) -> None:
        execution = Execution(
            execution_id="exec-1", plan_id="plan-1", action="execute", confidence=1.1
        )

        assert engine.validate(execution) is False

    def test_confidence_boundaries_are_accepted(self, engine: ExecutionEngine) -> None:
        assert (
            engine.validate(
                Execution(
                    execution_id="exec-1",
                    plan_id="plan-1",
                    action="execute",
                    confidence=0.0,
                )
            )
            is True
        )
        assert (
            engine.validate(
                Execution(
                    execution_id="exec-1",
                    plan_id="plan-1",
                    action="execute",
                    confidence=1.0,
                )
            )
            is True
        )


class TestExplain:
    """Tests for explanation generation."""

    def test_explain_describes_execution(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        explanation = engine.explain(execution)

        assert execution.execution_id in explanation
        assert execution.plan_id in explanation
        assert "action 'execute'" in explanation
        assert "is COMPLETED" in explanation
        assert "success: True" in explanation
        assert "confidence 0.9" in explanation

    def test_explain_is_deterministic(self, engine: ExecutionEngine) -> None:
        execution = engine.execute(make_plan())

        assert engine.explain(execution) == engine.explain(execution)

    def test_explain_with_none_execution_raises_value_error(
        self, engine: ExecutionEngine
    ) -> None:
        with pytest.raises(ValueError, match="execution is required"):
            engine.explain(None)  # type: ignore[arg-type]


class TestSupports:
    """Tests for the supports helper."""

    def test_supports_returns_all_statuses(self, engine: ExecutionEngine) -> None:
        assert engine.supports() == EXECUTION_STATUSES

    def test_supports_result_is_a_collection(self, engine: ExecutionEngine) -> None:
        supported = engine.supports()

        assert isinstance(supported, frozenset)
        for status in (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED):
            assert status in supported

    def test_supports_is_deterministic(self, engine: ExecutionEngine) -> None:
        assert engine.supports() == engine.supports()


class TestHealthCheck:
    """Tests for the engine health check."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, engine: ExecutionEngine) -> None:
        assert await engine.health_check() == {"healthy": True}
