"""Unit tests for the ExecutionEngine."""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.coding_adapter import CodingAdapter
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask
from kernel.intelligence.context import Context
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
from kernel.intelligence.plan import (
    DEFER,
    DENY,
    EXECUTE,
    REQUEST_CONFIRMATION,
    UNKNOWN,
    Plan,
)


def make_plan(
    goal: str = "Resolve intent 'chat' with action 'execute'",
    action: str = EXECUTE,
    priority: int = 1,
    confidence: float = 0.9,
    intent: str = "chat",
) -> Plan:
    """Build a Plan for execution tests."""
    return Plan(
        goal=goal,
        action=action,
        priority=priority,
        requires_confirmation=False,
        confidence=confidence,
        steps=("Validate decision", "Execute task"),
        metadata={"decision_action": "execute", "intent": intent},
    )


def make_context(
    *,
    user_input: str = "Research JARVIS",
    conversation_id: str = "conv-1",
    session_id: str = "session-1",
    working_memory: dict | None = None,
    environment: dict | None = None,
    metadata: dict | None = None,
) -> Context:
    """Build a Context for execution tests."""
    return Context(
        user_input=user_input,
        conversation_id=conversation_id,
        session_id=session_id,
        working_memory=working_memory or {"topic": "JARVIS"},
        environment=environment or {"os": "macOS"},
        metadata=metadata or {"source": "test"},
    )


@pytest.fixture
def engine() -> ExecutionEngine:
    """Provide an ExecutionEngine without a capability port."""
    return ExecutionEngine()


@pytest_asyncio.fixture
async def capability_engine() -> ExecutionEngine:
    """Provide an ExecutionEngine wired to a real CapabilityAdapterManager."""
    adapters = CapabilityAdapterManager()
    research = ResearchAdapter()
    await research.initialize()
    adapters.register(research)
    return ExecutionEngine(capabilities=adapters)


class TestExecuteSuccess:
    """Tests for successful execution."""

    @pytest.mark.asyncio
    async def test_valid_plan_completes(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

        assert execution.status == COMPLETED
        assert execution.success is True

    @pytest.mark.asyncio
    async def test_action_is_propagated(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan(action="defer"))

        assert execution.action == "defer"

    @pytest.mark.asyncio
    async def test_returns_execution_instance(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

        assert isinstance(execution, Execution)


class TestExecuteFailure:
    """Tests for failed execution."""

    @pytest.mark.asyncio
    async def test_invalid_plan_fails(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan(goal=""))

        assert execution.status == FAILED
        assert execution.success is False

    @pytest.mark.asyncio
    async def test_none_plan_fails(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(None)  # type: ignore[arg-type]

        assert execution.status == FAILED
        assert execution.success is False
        assert execution.action == "unknown"
        assert execution.confidence == 0.0

    @pytest.mark.asyncio
    async def test_failed_execution_is_never_successful(
        self, engine: ExecutionEngine
    ) -> None:
        for plan in [make_plan(goal=""), make_plan(action="")]:
            execution = await engine.execute(plan)

            assert execution.status == FAILED
            assert execution.success is False


class TestExecuteConfidence:
    """Tests for confidence propagation."""

    @pytest.mark.asyncio
    async def test_confidence_is_copied_from_plan(
        self, engine: ExecutionEngine
    ) -> None:
        execution = await engine.execute(make_plan(confidence=0.5))

        assert execution.confidence == 0.5

    @pytest.mark.asyncio
    async def test_boundary_confidences_are_preserved(
        self, engine: ExecutionEngine
    ) -> None:
        assert (await engine.execute(make_plan(confidence=0.0))).confidence == 0.0
        assert (await engine.execute(make_plan(confidence=1.0))).confidence == 1.0


class TestExecuteMetadata:
    """Tests for execution metadata."""

    @pytest.mark.asyncio
    async def test_metadata_includes_plan_action_and_goal(
        self, engine: ExecutionEngine
    ) -> None:
        plan = make_plan(goal="Resolve intent 'code' with action 'execute'")
        execution = await engine.execute(plan)

        assert execution.metadata == {
            "plan_action": EXECUTE,
            "goal": "Resolve intent 'code' with action 'execute'",
        }


class TestCapabilityExecution:
    """Tests for the capability execution boundary."""

    @pytest.mark.asyncio
    async def test_execute_plan_dispatches_to_capability_manager(
        self, capability_engine: ExecutionEngine
    ) -> None:
        execution = await capability_engine.execute(
            make_plan(
                goal="Resolve intent 'research' with action 'execute'",
                intent="research",
            ),
            make_context(),
        )

        assert execution.status == COMPLETED
        assert execution.success is True
        assert execution.metadata["capability"] == "research"
        assert execution.metadata["adapter"] == "research"
        assert execution.metadata["capability_result"]["intent"] == "research"

    @pytest.mark.asyncio
    async def test_execute_plan_populates_task_payload_from_context(
        self, capability_engine: ExecutionEngine
    ) -> None:
        context = make_context(
            user_input="Research JARVIS",
            working_memory={"topic": "JARVIS"},
        )

        execution = await capability_engine.execute(
            make_plan(intent="research"),
            context,
        )

        payload = execution.metadata["capability_result"]["payload"]
        assert payload == {
            "user_input": "Research JARVIS",
            "working_memory": {"topic": "JARVIS"},
        }

    @pytest.mark.asyncio
    async def test_execute_plan_populates_task_context_from_context(
        self, capability_engine: ExecutionEngine
    ) -> None:
        context = make_context(environment={"os": "macOS"})

        execution = await capability_engine.execute(
            make_plan(intent="research"),
            context,
        )

        task_context = execution.metadata["capability_result"]["context"]
        assert task_context["environment"] == {"os": "macOS"}
        assert task_context["timestamp"] == context.timestamp.isoformat()

    @pytest.mark.asyncio
    async def test_execute_plan_context_reaches_adapter_unchanged(
        self, capability_engine: ExecutionEngine
    ) -> None:
        context = make_context()

        execution = await capability_engine.execute(
            make_plan(intent="research"),
            context,
        )

        payload = execution.metadata["capability_result"]["payload"]
        task_context = execution.metadata["capability_result"]["context"]
        assert payload["working_memory"] == {"topic": "JARVIS"}
        assert task_context["environment"] == {"os": "macOS"}
        assert execution.metadata["capability_result"]["intent"] == "research"

    @pytest.mark.asyncio
    async def test_execute_plan_without_context_preserves_empty_task_fields(
        self, capability_engine: ExecutionEngine
    ) -> None:
        execution = await capability_engine.execute(make_plan(intent="research"))

        payload = execution.metadata["capability_result"]["payload"]
        task_context = execution.metadata["capability_result"]["context"]
        assert payload == {}
        assert task_context == {}

    @pytest.mark.asyncio
    async def test_execute_plan_does_not_mutate_context(
        self, capability_engine: ExecutionEngine
    ) -> None:
        context = make_context()

        await capability_engine.execute(make_plan(intent="research"), context)

        assert context.user_input == "Research JARVIS"
        assert context.conversation_id == "conv-1"
        assert context.session_id == "session-1"
        assert context.working_memory == {"topic": "JARVIS"}
        assert context.environment == {"os": "macOS"}
        assert context.metadata == {"source": "test"}

    @pytest.mark.asyncio
    async def test_execute_plan_unknown_capability_raises(
        self, capability_engine: ExecutionEngine
    ) -> None:
        with pytest.raises(ValueError, match="Unknown capability: does-not-exist"):
            await capability_engine.execute(
                make_plan(
                    goal="Resolve intent 'does-not-exist' with action 'execute'",
                    intent="does-not-exist",
                )
            )

    @pytest.mark.asyncio
    async def test_intent_supported_by_adapter_dispatches_even_when_names_differ(
        self,
    ) -> None:
        """Regression: 'code' is not an adapter name ('coding') but the coding
        adapter supports() it, so the boundary must dispatch, not reject."""
        adapters = CapabilityAdapterManager()
        coding = CodingAdapter()
        await coding.initialize()
        adapters.register(coding)

        execution = await ExecutionEngine(capabilities=adapters).execute(
            make_plan(
                goal="Resolve intent 'code' with action 'execute'",
                intent="code",
            )
        )

        assert execution.status == COMPLETED
        assert execution.success is True
        assert execution.metadata["capability"] == "code"
        assert execution.metadata["adapter"] == "coding"

    @pytest.mark.asyncio
    async def test_failed_capability_result_records_failed(self) -> None:
        capabilities = MagicMock()
        capabilities.can_handle.return_value = True
        capabilities.execute = AsyncMock(
            return_value=CapabilityResult(
                success=False,
                data=None,
                error="adapter error",
            )
        )

        execution = await ExecutionEngine(capabilities=capabilities).execute(
            make_plan(intent="research")
        )

        assert execution.status == FAILED
        assert execution.success is False
        assert execution.metadata["capability"] == "research"

    @pytest.mark.asyncio
    async def test_non_execute_plan_does_not_dispatch(self) -> None:
        capabilities = MagicMock()
        capabilities.can_handle.return_value = True

        execution = await ExecutionEngine(capabilities=capabilities).execute(
            make_plan(action="defer", intent="research")
        )

        assert execution.status == PENDING
        assert execution.success is False
        assert "adapter" not in execution.metadata
        capabilities.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_port_records_without_dispatch(
        self, engine: ExecutionEngine
    ) -> None:
        execution = await engine.execute(
            make_plan(goal="Resolve intent 'research' with action 'execute'")
        )

        assert execution.status == COMPLETED
        assert execution.success is True
        assert "adapter" not in execution.metadata


class TestNonExecuteSemantics:
    """Tests for the waiting-state semantics of non-EXECUTE plans.

    Waiting plans (request_confirmation, defer, unknown) represent work
    waiting on an external actor: they are recorded as PENDING with
    success False, never COMPLETED, and never dispatch. Denial remains a
    terminal completed outcome.
    """

    async def execute_waiting(
        self,
        action: str,
        capabilities: MagicMock | None = None,
    ) -> Execution:
        port = capabilities or MagicMock()
        port.can_handle.return_value = True
        return await ExecutionEngine(capabilities=port).execute(
            make_plan(action=action, intent="research")
        )

    @pytest.mark.parametrize(
        ("plan_action", "decision"),
        [
            (REQUEST_CONFIRMATION, "ask_confirmation"),
            (REQUEST_CONFIRMATION, "ask_clarification"),
            (DEFER, "defer"),
            (UNKNOWN, "noop"),
        ],
    )
    @pytest.mark.asyncio
    async def test_waiting_actions_never_dispatch(
        self, plan_action: str, decision: str
    ) -> None:
        capabilities = MagicMock()
        capabilities.can_handle.return_value = True

        await ExecutionEngine(capabilities=capabilities).execute(
            make_plan(action=plan_action, intent="research")
        )

        capabilities.execute.assert_not_called()

    @pytest.mark.parametrize(
        ("plan_action", "decision"),
        [
            (REQUEST_CONFIRMATION, "ask_confirmation"),
            (REQUEST_CONFIRMATION, "ask_clarification"),
            (DEFER, "defer"),
            (UNKNOWN, "noop"),
        ],
    )
    @pytest.mark.asyncio
    async def test_waiting_actions_are_pending_and_unsuccessful(
        self, plan_action: str, decision: str
    ) -> None:
        execution = await self.execute_waiting(plan_action)

        assert execution.action == plan_action
        assert execution.status == PENDING
        assert execution.status != COMPLETED
        assert execution.success is False
        assert "adapter" not in execution.metadata

    @pytest.mark.asyncio
    async def test_ask_confirmation_never_returns_completed(self) -> None:
        execution = await self.execute_waiting(REQUEST_CONFIRMATION)

        assert execution.status == PENDING
        assert execution.status != COMPLETED

    @pytest.mark.asyncio
    async def test_ask_confirmation_never_returns_success(self) -> None:
        execution = await self.execute_waiting(REQUEST_CONFIRMATION)

        assert execution.success is False

    @pytest.mark.asyncio
    async def test_denial_is_terminal_and_completed(self) -> None:
        execution = await self.execute_waiting(DENY)

        assert execution.action == DENY
        assert execution.status == COMPLETED
        assert execution.success is True
        assert "adapter" not in execution.metadata


class TestContextToTask:
    """Tests that Context-derived data populates the CapabilityTask."""

    async def capture_task(self, context: Context | None) -> CapabilityTask:
        captured: list[CapabilityTask] = []

        class CapturingCapabilities:
            def can_handle(self, intent: str) -> bool:
                return True

            async def execute(self, task: CapabilityTask) -> CapabilityResult:
                captured.append(task)
                return CapabilityResult(success=True, data={"intent": task.intent})

        await ExecutionEngine(capabilities=CapturingCapabilities()).execute(
            make_plan(intent="research"),
            context,
        )

        return captured[0]

    @pytest.mark.asyncio
    async def test_task_metadata_includes_conversation_and_session(
        self,
    ) -> None:
        task = await self.capture_task(
            make_context(conversation_id="conv-42", session_id="session-42")
        )

        assert task.metadata["conversation_id"] == "conv-42"
        assert task.metadata["session_id"] == "session-42"

    @pytest.mark.asyncio
    async def test_task_metadata_includes_context_metadata(self) -> None:
        task = await self.capture_task(
            make_context(metadata={"source": "test", "channel": "cli"})
        )

        assert task.metadata["source"] == "test"
        assert task.metadata["channel"] == "cli"

    @pytest.mark.asyncio
    async def test_task_metadata_keeps_plan_fields_authoritative(self) -> None:
        task = await self.capture_task(
            make_context(metadata={"plan_id": "spoofed", "goal": "spoofed"})
        )

        assert task.metadata["plan_id"] == task.task_id.replace("task-", "plan-")
        assert task.metadata["goal"] == make_plan().goal
        assert task.metadata["plan_action"] == EXECUTE

    @pytest.mark.asyncio
    async def test_task_metadata_without_context_has_no_identifiers(self) -> None:
        task = await self.capture_task(None)

        assert task.metadata["plan_id"].startswith("plan-")
        assert task.metadata["goal"] == make_plan().goal
        assert "conversation_id" not in task.metadata
        assert "session_id" not in task.metadata


class TestDeterministicIds:
    """Tests for deterministic identifier generation."""

    @pytest.mark.asyncio
    async def test_same_plan_produces_same_ids(self, engine: ExecutionEngine) -> None:
        plan = make_plan()

        first = await engine.execute(plan)
        second = await engine.execute(plan)

        assert first.execution_id == second.execution_id
        assert first.plan_id == second.plan_id

    @pytest.mark.asyncio
    async def test_different_plans_produce_different_ids(
        self, engine: ExecutionEngine
    ) -> None:
        first = await engine.execute(make_plan(goal="goal a"))
        second = await engine.execute(make_plan(goal="goal b"))

        assert first.execution_id != second.execution_id

    @pytest.mark.asyncio
    async def test_ids_are_prefixed(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

        assert execution.execution_id.startswith("exec-")
        assert execution.plan_id.startswith("plan-")

    @pytest.mark.asyncio
    async def test_none_plan_has_stable_unknown_id(
        self, engine: ExecutionEngine
    ) -> None:
        first = await engine.execute(None)  # type: ignore[arg-type]
        second = await engine.execute(None)  # type: ignore[arg-type]

        assert first.execution_id == second.execution_id == "exec-unknown"
        assert first.plan_id == second.plan_id == "plan-unknown"

    @pytest.mark.asyncio
    async def test_execution_is_fully_deterministic(
        self, engine: ExecutionEngine
    ) -> None:
        plan = make_plan()

        assert await engine.execute(plan) == await engine.execute(plan)


class TestValidate:
    """Tests for execution validation."""

    @pytest.mark.asyncio
    async def test_valid_execution_is_accepted(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

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

    @pytest.mark.asyncio
    async def test_explain_describes_execution(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

        explanation = engine.explain(execution)

        assert execution.execution_id in explanation
        assert execution.plan_id in explanation
        assert "action 'execute'" in explanation
        assert "is COMPLETED" in explanation
        assert "success: True" in explanation
        assert "confidence 0.9" in explanation

    @pytest.mark.asyncio
    async def test_explain_is_deterministic(self, engine: ExecutionEngine) -> None:
        execution = await engine.execute(make_plan())

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
