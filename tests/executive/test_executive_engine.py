"""Tests for the ExecutiveEngine intelligence pipeline and capability execution."""

from __future__ import annotations

import hashlib
from typing import Any

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.adapters.coding_adapter import CodingAdapter
from kernel.adapters.browser_adapter import BrowserAdapter
from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.adapters.voice_adapter import VoiceAdapter
from kernel.adapters.memory_adapter import MemoryAdapter
from kernel.events.event import Event
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.policy import PolicyEngine, PolicyRule
from kernel.interfaces.browser_backend import BrowserBackend, BrowserResult
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask
from kernel.interfaces.research_backend import ResearchResult
from kernel.memory.memory_manager import MemoryManager
from kernel.storage.sqlite_memory_store import SQLiteMemoryStore
from kernel.storage.storage_manager import StorageManager
from kernel.security.security_manager import SecurityManager
from kernel.tools.tool_registry import ToolRegistry
from kernel.workflow.workflow_manager import WorkflowManager
from kernel.config.config_manager import ConfigManager


class FakeBrowserBackend:
    """Fake browser backend for testing."""

    def __init__(self) -> None:
        self._initialized = False
        self.calls: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False

    async def health_check(self) -> bool:
        return self._initialized

    async def navigate(self, url: str, *, timeout: Optional[float] = None) -> BrowserResult:
        self.calls.append({"method": "navigate", "url": url, "timeout": timeout})
        return BrowserResult(success=True, url=url, title="Test Page", content="Test content")

    async def search(self, query: str, *, limit: int = 10, timeout: Optional[float] = None) -> BrowserResult:
        self.calls.append({"method": "search", "query": query, "limit": limit, "timeout": timeout})
        return BrowserResult(
            success=True,
            url="https://www.bing.com/search?q=test",
            title=f"Search results for: {query}",
            content="Test results",
            data={"results": [{"title": "Test", "url": "https://example.com", "snippet": "Test snippet"}]},
        )

    async def extract(self, selector: Optional[str] = None) -> BrowserResult:
        self.calls.append({"method": "extract", "selector": selector})
        return BrowserResult(success=True, url="https://example.com", title="Test Page", content="Extracted content")

    async def screenshot(self, *, full_page: bool = False) -> BrowserResult:
        self.calls.append({"method": "screenshot", "full_page": full_page})
        return BrowserResult(success=True, data={"screenshot": b"fake", "full_page": full_page})
from typing import Any, Optional
from kernel.models.model_manager import ModelManager

from kernel.intelligence.context_engine import ContextEngine
from kernel.intelligence.intent_engine import IntentEngine
from kernel.intelligence.reasoning_engine import ReasoningEngine
from kernel.intelligence.decision_engine import DecisionEngine
from kernel.intelligence.planning_engine import PlanningEngine
from kernel.intelligence.execution_engine import ExecutionEngine
from kernel.intelligence.intent import Intent
from kernel.intelligence.reasoning import Reasoning
from kernel.intelligence.decision import Decision
from kernel.intelligence.plan import Plan
from kernel.intelligence.execution import Execution

# Optional integrations
from kernel.environment.digital_twin import DigitalTwin
from kernel.observability.observability_manager import ObservabilityManager
from kernel.plugin.plugin_manager import PluginManager
from kernel.recovery.recovery_manager import RecoveryManager


def _assert_event_args(args: tuple, event_name: str, expected_payload: dict[str, Any]) -> None:
    """Assert that publish was called with an Event matching the expected name and payload."""
    assert len(args) == 1
    event = args[0]
    assert isinstance(event, Event)
    assert event.name == event_name
    assert event.payload == expected_payload


class FakeResearchBackend:
    """Deterministic in-memory ResearchBackend for tests."""

    async def search(self, query: str, **kwargs: Any) -> list[ResearchResult]:
        return [
            ResearchResult(
                title="JARVIS",
                snippet=f"Result for {query}",
                url="https://example.com/jarvis",
                source="fake",
            )
        ]


@pytest_asyncio.fixture
async def executive_engine(tmp_path) -> ExecutiveEngine:
    adapters = CapabilityAdapterManager()
    research = ResearchAdapter(FakeResearchBackend())
    await research.initialize()
    adapters.register(research)

    coding = CodingAdapter()
    await coding.initialize()
    adapters.register(coding)

    browser_backend = FakeBrowserBackend()
    browser = BrowserAdapter(backend=browser_backend)
    await browser.initialize()
    adapters.register(browser)

    store = SQLiteMemoryStore(":memory:")
    memory = MemoryManager(store)

    workspace = WorkspaceAdapter(StorageManager(tmp_path / "workspace"))
    await workspace.initialize()
    adapters.register(workspace)

    voice = VoiceAdapter()
    await voice.initialize()
    adapters.register(voice)

    memory_adapter = MemoryAdapter(memory)
    await memory_adapter.initialize()
    adapters.register(memory_adapter)

    events = AsyncMock()

    config = ConfigManager()
    models = ModelManager()

    policy = PolicyEngine(
        [
            PolicyRule(intent="chat", allowed=True),
            PolicyRule(intent="speech_to_text", allowed=True),
            PolicyRule(intent="remember", allowed=True),
            PolicyRule(intent="recall", allowed=True),
            PolicyRule(intent="search_memory", allowed=True),
            PolicyRule(intent="forget", allowed=True),
            PolicyRule(intent="research", allowed=True),
            PolicyRule(intent="generate_code", allowed=True),
            PolicyRule(intent="web_search", allowed=True),
            PolicyRule(intent="read_file", allowed=True),
            PolicyRule(intent="write_file", allowed=True),
            PolicyRule(intent="move_file", allowed=True),
            PolicyRule(intent="delete_file", allowed=True),
            PolicyRule(intent="create_directory", allowed=True),
            PolicyRule(intent="list_directory", allowed=True),
        ]
    )

    engine = ExecutiveEngine(
        memory=memory,
        workflows=WorkflowManager(),
        tools=ToolRegistry(),
        adapters=adapters,
        events=events,
        security=SecurityManager(),
        config=config,
        models=models,
        policy=policy,
        context_engine=ContextEngine(),
        intent_engine=IntentEngine(),
        reasoning_engine=ReasoningEngine(),
        decision_engine=DecisionEngine(),
        planning_engine=PlanningEngine(),
        execution_engine=ExecutionEngine(capabilities=adapters),
    )

    try:
        yield engine
    finally:
        await store.close()


def make_execution(
    *,
    success: bool = True,
    status: str = "completed",
) -> Execution:
    return Execution(
        execution_id="exec-1",
        plan_id="plan-1",
        action="execute",
        status=status,
        success=success,
        confidence=0.9,
        metadata={"plan_action": "execute", "goal": "research"},
    )


# ---------------------------------------------------------------------------
# Capability execution path (unchanged)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_voice_capability(
    executive_engine: ExecutiveEngine,
) -> None:
    result = await executive_engine.execute_capability(
        "speech_to_text",
        {"audio": "sample.wav"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "voice"
    assert result.data["intent"] == "speech_to_text"
    assert result.data["payload"] == {"audio": "sample.wav"}
    assert result.data["message"] == "Speech-to-text placeholder."


@pytest.mark.asyncio
async def test_execute_memory_capability(
    executive_engine: ExecutiveEngine,
) -> None:
    result = await executive_engine.execute_capability(
        "remember",
        {"key": "greeting", "value": "Hello JARVIS"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.metadata["status"] == "ok"
    assert result.data["intent"] == "remember"
    assert result.data["key"] == "greeting"

    recalled = await executive_engine.execute_capability(
        "recall",
        {"key": "greeting"},
    )

    assert recalled.success is True
    assert recalled.data["value"] == "Hello JARVIS"


@pytest.mark.asyncio
async def test_execute_research_capability(executive_engine: ExecutiveEngine) -> None:
    result = await executive_engine.execute_capability(
        "research",
        {"query": "JARVIS"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "research"
    assert result.data["intent"] == "research"


@pytest.mark.asyncio
async def test_execute_coding_capability(executive_engine: ExecutiveEngine) -> None:
    result = await executive_engine.execute_capability(
        "generate_code",
        {"prompt": "print('Hello, JARVIS')"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "coding"
    assert result.data["intent"] == "generate_code"
    assert result.data["payload"] == {"prompt": "print('Hello, JARVIS')"}
    assert "Generated code" in result.data["message"]


@pytest.mark.asyncio
async def test_execute_browser_capability(executive_engine: ExecutiveEngine) -> None:
    result = await executive_engine.execute_capability(
        "web_search",
        {"query": "JARVIS"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "browser"
    assert result.data["intent"] == "web_search"
    assert result.data["payload"] == {"query": "JARVIS"}
    assert result.data["url"] == "https://www.bing.com/search?q=test"
    assert result.data["title"] == "Search results for: JARVIS"


@pytest.mark.asyncio
async def test_execute_workspace_capability(
    executive_engine: ExecutiveEngine,
) -> None:
    write = await executive_engine.execute_capability(
        "write_file",
        {"path": "README.md", "content": "JARVIS README"},
    )

    assert isinstance(write, CapabilityResult)
    assert write.success is True
    assert write.metadata["adapter"] == "workspace"
    assert write.metadata["status"] == "ok"
    assert write.data["intent"] == "write_file"

    result = await executive_engine.execute_capability(
        "read_file",
        {"path": "README.md"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "workspace"
    assert result.data["intent"] == "read_file"
    assert result.data["content"] == "JARVIS README"


@pytest.mark.asyncio
async def test_execute_unknown_capability_raises(
    executive_engine: ExecutiveEngine,
) -> None:
    with pytest.raises(
        PermissionError,
        match="No policy rule registered",
    ):
        await executive_engine.execute_capability(
            "does-not-exist",
            {},
        )


# Policy tests


@pytest.mark.asyncio
async def test_policy_denied_blocks_execution(
    executive_engine: ExecutiveEngine,
) -> None:
    executive_engine.policy.register(
        PolicyRule(intent="blocked.intent", allowed=False, reason="Blocked by policy")
    )

    with pytest.raises(PermissionError, match="Blocked by policy"):
        await executive_engine.execute_capability("blocked.intent", {})


@pytest.mark.asyncio
async def test_policy_requires_approval_blocks_execution(
    executive_engine: ExecutiveEngine,
) -> None:
    executive_engine.policy.register(
        PolicyRule(
            intent="approval.intent",
            allowed=True,
            requires_approval=True,
            reason="Approval required",
        )
    )

    with pytest.raises(PermissionError, match="requires approval"):
        await executive_engine.execute_capability("approval.intent", {})


def test_policy_property_returns_engine_policy(
    executive_engine: ExecutiveEngine,
) -> None:
    assert isinstance(executive_engine.policy, PolicyEngine)


# ---------------------------------------------------------------------------
# Intelligence pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_request_runs_intelligence_pipeline(
    executive_engine: ExecutiveEngine,
) -> None:
    results = await executive_engine.execute_request("Research JARVIS")

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.data["action"] == "execute"
    assert result.data["status"] == "COMPLETED"
    assert result.data["plan_id"].startswith("plan-")
    assert result.data["execution_id"].startswith("exec-")
    assert result.metadata["plan_action"] == "execute"
    assert result.metadata["capability"] == "research"
    assert result.metadata["adapter"] == "research"


@pytest.mark.asyncio
async def test_execute_request_code_intent_dispatches_to_coding_adapter(
    executive_engine: ExecutiveEngine,
) -> None:
    """Regression: intent 'code' is not an adapter name ('coding'), so it must
    route via supports() resolution, not the name-based registry lookup."""
    executive_engine.policy.register(PolicyRule(intent="code", allowed=True))

    results = await executive_engine.execute_request("Write a python script")

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.data["action"] == "execute"
    assert result.data["status"] == "COMPLETED"
    assert result.metadata["capability"] == "code"
    assert result.metadata["adapter"] == "coding"


@pytest.mark.asyncio
async def test_execute_request_remember_intent_dispatches_to_memory_adapter(
    executive_engine: ExecutiveEngine,
) -> None:
    """Regression: the Intelligence Layer must emit a canonical capability
    name ('remember') that the memory adapter actually supports, instead of
    the collapsed 'memory' capability that failed at execution time."""
    results = await executive_engine.execute_request(
        "Remember my favorite color is blue"
    )

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.data["action"] == "execute"
    assert result.data["status"] == "COMPLETED"
    assert result.metadata["capability"] == "remember"
    assert result.metadata["adapter"] == "memory"


@pytest.mark.asyncio
async def test_execute_request_remember_pipeline_persists_real_memory(
    executive_engine: ExecutiveEngine,
) -> None:
    """The intelligence pipeline must persist a memory through the real
    MemoryManager: Natural Language -> ExecutiveEngine -> ExecutionEngine ->
    CapabilityAdapterManager -> MemoryAdapter -> MemoryManager -> MemoryStore."""
    objective = "Remember my favorite color is blue"

    results = await executive_engine.execute_request(objective)

    assert results[0].success is True
    assert results[0].data["status"] == "COMPLETED"
    assert results[0].metadata["capability"] == "remember"
    assert results[0].metadata["adapter"] == "memory"

    searched = await executive_engine.execute_capability(
        "search_memory", {"query": "favorite color"}
    )
    assert searched.success is True
    assert objective in searched.data["results"]

    derived_key = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:16]

    forgotten = await executive_engine.execute_capability(
        "forget", {"key": derived_key}
    )
    assert forgotten.success is True

    missing = await executive_engine.execute_capability("recall", {"key": derived_key})
    assert missing.success is False
    assert "Memory not found" in missing.error


@pytest.mark.asyncio
async def test_execute_request_memory_search_pipeline_reaches_store(
    executive_engine: ExecutiveEngine,
) -> None:
    """search_memory through the full ExecutiveEngine path must search the
    real MemoryStore."""
    await executive_engine.execute_capability(
        "remember", {"key": "color", "value": "blue"}
    )
    await executive_engine.execute_capability(
        "remember", {"key": "song", "value": "blue moon"}
    )

    results = await executive_engine.execute_request("Search my memory for blue")

    assert results[0].success is True
    assert results[0].data["status"] == "COMPLETED"
    assert results[0].metadata["capability"] == "search_memory"
    assert results[0].metadata["adapter"] == "memory"

    searched = await executive_engine.execute_capability(
        "search_memory", {"query": "blue"}
    )
    assert searched.success is True
    assert len(searched.data["results"]) == 2
    assert set(searched.data["results"]) == {"blue", "blue moon"}


@pytest.mark.asyncio
async def test_workspace_lifecycle_through_executive_engine(
    executive_engine: ExecutiveEngine,
) -> None:
    """Every workspace operation executes through ExecutiveEngine ->
    CapabilityAdapterManager -> WorkspaceAdapter -> StorageManager."""
    written = await executive_engine.execute_capability(
        "write_file", {"path": "notes.txt", "content": "content"}
    )
    assert written.success is True

    listed = await executive_engine.execute_capability("list_directory", {})
    assert listed.success is True
    assert listed.data["entries"] == ["notes.txt"]

    directory = await executive_engine.execute_capability(
        "create_directory", {"path": "archive"}
    )
    assert directory.success is True

    moved = await executive_engine.execute_capability(
        "move_file",
        {"source": "notes.txt", "destination": "archive/notes.txt"},
    )
    assert moved.success is True

    read = await executive_engine.execute_capability(
        "read_file", {"path": "archive/notes.txt"}
    )
    assert read.success is True
    assert read.data["content"] == "content"

    deleted = await executive_engine.execute_capability(
        "delete_file", {"path": "archive/notes.txt"}
    )
    assert deleted.success is True

    missing = await executive_engine.execute_capability(
        "read_file", {"path": "archive/notes.txt"}
    )
    assert missing.success is False
    assert "File not found" in missing.error


@pytest.mark.asyncio
async def test_execute_request_voice_intent_dispatches_to_voice_adapter(
    executive_engine: ExecutiveEngine,
) -> None:
    """Regression: a voice request must classify to the 'voice' intent and
    dispatch to the voice adapter through the capability boundary."""
    executive_engine.policy.register(PolicyRule(intent="voice", allowed=True))

    results = await executive_engine.execute_request("transcribe this audio")

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.data["action"] == "execute"
    assert result.data["status"] == "COMPLETED"
    assert result.metadata["capability"] == "voice"
    assert result.metadata["adapter"] == "voice"


@pytest.mark.asyncio
async def test_execute_request_workspace_intent_is_reachable(
    executive_engine: ExecutiveEngine,
) -> None:
    """Regression: the workspace adapter must accept the 'workspace' intent
    the Intelligence Layer emits, so the capability is reachable at the
    execution boundary. Workspace requests pause for confirmation by design."""
    executive_engine.policy.register(PolicyRule(intent="workspace", allowed=True))

    assert executive_engine.adapters.can_handle("workspace") is True

    results = await executive_engine.execute_request("open my project")

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is False
    assert result.data["action"] == "request_confirmation"
    assert result.data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_execute_request_pipeline_stage_order() -> None:
    order: list[str] = []

    def track(name: str, value: Any) -> Any:
        def side_effect(*args: Any, **kwargs: Any) -> Any:
            order.append(name)
            return value

        return side_effect

    context_engine = MagicMock()
    built_context = MagicMock()
    context_engine.build.side_effect = track("context", built_context)

    intent_engine = MagicMock()
    intent_engine.classify.side_effect = track(
        "intent",
        Intent(name="research", confidence=0.9, parameters={}),
    )

    reasoning_engine = MagicMock()
    reasoning_engine.reason.side_effect = track(
        "reasoning",
        Reasoning(
            intent_name="research",
            capability="research",
            explanation="test",
            priority="NORMAL",
            requires_confirmation=False,
        ),
    )

    decision_engine = MagicMock()
    decision_engine.decide.side_effect = track(
        "decision",
        Decision(
            action="execute",
            confidence=0.9,
            requires_confirmation=False,
            explanation="test",
            metadata={
                "intent": "research",
                "capability": "research",
                "priority": "NORMAL",
            },
        ),
    )

    planning_engine = MagicMock()
    planning_engine.create_plan.side_effect = track(
        "planning",
        Plan(
            goal="Resolve intent 'research' with action 'execute'",
            action="execute",
            priority=1,
            requires_confirmation=False,
            confidence=0.9,
            steps=("execute",),
            metadata={"decision_action": "execute", "intent": "research"},
        ),
    )
    planning_engine.validate.side_effect = track("validate", True)

    execution_engine = MagicMock()
    execution_engine.execute = AsyncMock(
        side_effect=track("execution", make_execution())
    )

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter())

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=context_engine,
            intent_engine=intent_engine,
            reasoning_engine=reasoning_engine,
            decision_engine=decision_engine,
            planning_engine=planning_engine,
            execution_engine=execution_engine,
        )

        results = await engine.execute_request("Research JARVIS")

        assert order == [
            "context",
            "intent",
            "reasoning",
            "decision",
            "planning",
            "validate",
            "execution",
        ]
        assert results[0].success is True
        assert results[0].data["execution_id"] == "exec-1"

        # The Context built by ContextEngine must reach the ExecutionEngine
        # unchanged, and the intelligence stages must not receive it.
        assert execution_engine.execute.await_args.args[0] is not None
        assert execution_engine.execute.await_args.args[1] is built_context
        context_engine.build.assert_called_once()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_invalid_plan_raises() -> None:
    planning_engine = MagicMock()
    planning_engine.create_plan.return_value = MagicMock()
    planning_engine.validate.return_value = False

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=planning_engine,
            execution_engine=ExecutionEngine(),
        )

        with pytest.raises(ValueError, match="failed validation"):
            await engine.execute_request("Research JARVIS")
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_unknown_capability_raises() -> None:
    decision_engine = MagicMock()
    decision_engine.decide.return_value = Decision(
        action="execute",
        confidence=0.9,
        requires_confirmation=False,
        explanation="test",
        metadata={
            "intent": "does-not-exist",
            "capability": "does-not-exist",
            "priority": "NORMAL",
        },
    )

    adapters = CapabilityAdapterManager()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=decision_engine,
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        with pytest.raises(ValueError, match="Unknown capability: does-not-exist"):
            await engine.execute_request("Research JARVIS")
    finally:
        await store.close()


@pytest.mark.parametrize(
    "decision_action",
    [
        "ask_clarification",
        "ask_confirmation",
        "defer",
        "noop",
    ],
)
@pytest.mark.asyncio
async def test_execute_request_waiting_decision_never_completes(
    decision_action: str,
) -> None:
    decision_engine = MagicMock()
    decision_engine.decide.return_value = Decision(
        action=decision_action,
        confidence=0.4,
        requires_confirmation=decision_action
        in ("ask_confirmation", "ask_clarification"),
        explanation="test",
        metadata={
            "intent": "does-not-exist",
            "capability": "does-not-exist",
            "priority": "NORMAL",
        },
    )

    adapters = CapabilityAdapterManager()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=decision_engine,
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        results = await engine.execute_request("Research JARVIS")

        assert results[0].success is False
        assert results[0].data["status"] == "PENDING"
        assert "capability" not in results[0].metadata
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_reject_decision_is_terminal_completed() -> None:
    """Regression: a reject decision is a terminal outcome (the kernel
    completed its response); it is not a waiting state."""
    decision_engine = MagicMock()
    decision_engine.decide.return_value = Decision(
        action="reject",
        confidence=0.4,
        requires_confirmation=False,
        explanation="test",
        metadata={
            "intent": "does-not-exist",
            "capability": "does-not-exist",
            "priority": "NORMAL",
        },
    )

    adapters = CapabilityAdapterManager()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=decision_engine,
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        results = await engine.execute_request("Research JARVIS")

        assert results[0].success is True
        assert results[0].data["status"] == "COMPLETED"
        assert "capability" not in results[0].metadata
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_policy_denied() -> None:
    policy = PolicyEngine(
        [
            PolicyRule(intent="chat", allowed=False, reason="Blocked by policy"),
        ]
    )

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=policy,
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        with pytest.raises(PermissionError, match="Blocked by policy"):
            await engine.execute_request("Denied")
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_policy_denial_closes_request_lifecycle() -> None:
    """Regression: a policy denial must terminate the started request with
    request.failed and close observability — never leave it open."""
    policy = PolicyEngine(
        [
            PolicyRule(intent="chat", allowed=False, reason="Blocked by policy"),
        ]
    )
    events = AsyncMock()
    observability = MagicMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=events,
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=policy,
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            observability=observability,
        )

        with pytest.raises(PermissionError, match="Blocked by policy"):
            await engine.execute_request("Denied")

        assert events.publish.await_count == 2
        _assert_event_args(
            events.publish.await_args_list[0].args, "request.started", {"objective": "Denied"}
        )
        _assert_event_args(
            events.publish.await_args_list[1].args, "request.failed", {"objective": "Denied", "success": False}
        )
        observability.record_request_started.assert_called_once_with("Denied")
        observability.record_request_failed.assert_called_once_with("Denied")
        observability.record_request_completed.assert_not_called()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_authorization_denial_closes_request_lifecycle() -> None:
    """Regression: a security authorization denial must terminate the
    started request with request.failed and close observability."""
    security = MagicMock()
    security.authorize = AsyncMock(return_value=False)

    events = AsyncMock()
    observability = MagicMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=events,
            security=security,
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            observability=observability,
        )

        with pytest.raises(PermissionError, match="Execution denied"):
            await engine.execute_request("Research JARVIS")

        assert events.publish.await_count == 2
        _assert_event_args(
            events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
        )
        _assert_event_args(
            events.publish.await_args_list[1].args, "request.failed", {"objective": "Research JARVIS", "success": False}
        )
        observability.record_request_started.assert_called_once_with("Research JARVIS")
        observability.record_request_failed.assert_called_once_with("Research JARVIS")
        observability.record_request_completed.assert_not_called()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_policy_requires_approval() -> None:
    policy = PolicyEngine(
        [
            PolicyRule(
                intent="research",
                allowed=True,
                requires_approval=True,
                reason="Approval required",
            ),
        ]
    )

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=policy,
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        with pytest.raises(PermissionError, match="requires approval"):
            await engine.execute_request("Research JARVIS")
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_publishes_started_and_completed(
    executive_engine: ExecutiveEngine,
) -> None:
    await executive_engine.execute_request("Research JARVIS")

    assert executive_engine._events.publish.await_count == 2
    _assert_event_args(
        executive_engine._events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
    )
    _assert_event_args(
        executive_engine._events.publish.await_args_list[1].args, "request.completed", {"objective": "Research JARVIS", "success": True}
    )


@pytest.mark.asyncio
async def test_execute_request_publishes_failed_and_reraises(
    executive_engine: ExecutiveEngine,
) -> None:
    execution_error = RuntimeError("execution failed")
    failing_execution_engine = MagicMock()
    failing_execution_engine.execute.side_effect = execution_error
    executive_engine._execution_engine = failing_execution_engine

    with pytest.raises(RuntimeError) as exc_info:
        await executive_engine.execute_request("Research JARVIS")

    assert exc_info.value is execution_error
    assert executive_engine._events.publish.await_count == 2
    _assert_event_args(
        executive_engine._events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
    )
    _assert_event_args(
        executive_engine._events.publish.await_args_list[1].args, "request.failed", {"objective": "Research JARVIS", "success": False}
    )


def make_waiting_decision_engine(decision_action: str) -> MagicMock:
    """Provide a DecisionEngine that always returns a non-execute decision."""
    decision_engine = MagicMock()
    decision_engine.decide.return_value = Decision(
        action=decision_action,
        confidence=0.4,
        requires_confirmation=decision_action
        in ("ask_confirmation", "ask_clarification"),
        explanation="test",
        metadata={
            "intent": "does-not-exist",
            "capability": "does-not-exist",
            "priority": "NORMAL",
        },
    )
    return decision_engine


# ---------------------------------------------------------------------------
# Request lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_request_failed_execution_uses_failed_lifecycle() -> None:
    """Regression: a FAILED execution record (adapter failure, no exception)
    must publish request.failed and record request_failed — never the
    completed lifecycle."""
    failing_execution_engine = MagicMock()
    failing_execution_engine.execute = AsyncMock(
        return_value=make_execution(success=False, status="FAILED")
    )

    events = AsyncMock()
    observability = MagicMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=events,
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=failing_execution_engine,
            observability=observability,
        )

        results = await engine.execute_request("Research JARVIS")

        assert results[0].success is False
        assert events.publish.await_count == 2
        _assert_event_args(
            events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
        )
        _assert_event_args(
            events.publish.await_args_list[1].args, "request.failed", {"objective": "Research JARVIS", "success": False}
        )
        observability.record_request_started.assert_called_once_with("Research JARVIS")
        observability.record_request_failed.assert_called_once_with("Research JARVIS")
        observability.record_request_completed.assert_not_called()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_pending_never_uses_completed_lifecycle() -> None:
    """Regression: a PENDING execution (waiting on an external actor) must
    never publish request.completed and must never record request_completed."""
    decision_engine = make_waiting_decision_engine("ask_confirmation")

    events = AsyncMock()
    observability = MagicMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=events,
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=decision_engine,
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            observability=observability,
        )

        results = await engine.execute_request("Research JARVIS")

        assert results[0].data["status"] == "PENDING"
        assert results[0].success is False
        assert events.publish.await_count == 1
        _assert_event_args(
            events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
        )
        observability.record_request_started.assert_called_once_with("Research JARVIS")
        observability.record_request_completed.assert_not_called()
        observability.record_request_failed.assert_not_called()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_pending_defer_never_publishes_completed() -> None:
    """Regression: every waiting decision (defer) stays open, never closed
    as completed."""
    decision_engine = make_waiting_decision_engine("defer")

    events = AsyncMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=events,
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=decision_engine,
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        results = await engine.execute_request("Research JARVIS")

        assert results[0].data["status"] == "PENDING"
        assert events.publish.await_count == 1
        _assert_event_args(
            events.publish.await_args_list[0].args, "request.started", {"objective": "Research JARVIS"}
        )
        # Verify it's not a completed event
        event = events.publish.await_args_list[0].args[0]
        assert isinstance(event, Event)
        assert event.name != "request.completed"
    finally:
        await store.close()


# ---------------------------------------------------------------------------
# Optional integrations
# ---------------------------------------------------------------------------


def test_optional_integrations_default_to_none(
    executive_engine: ExecutiveEngine,
) -> None:
    assert executive_engine.plugins is None
    assert executive_engine.recovery is None
    assert executive_engine.observability is None
    assert executive_engine.digital_twin is None


@pytest.mark.asyncio
async def test_optional_integrations_are_stored() -> None:
    adapters = CapabilityAdapterManager()
    events = AsyncMock()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=events,
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine([]),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            plugins=PluginManager(),
            recovery=RecoveryManager(),
            observability=ObservabilityManager(),
            digital_twin=DigitalTwin(),
        )

        assert isinstance(engine.plugins, PluginManager)
        assert isinstance(engine.recovery, RecoveryManager)
        assert isinstance(engine.observability, ObservabilityManager)
        assert isinstance(engine.digital_twin, DigitalTwin)
    finally:
        await store.close()


# ---------------------------------------------------------------------------
# Observability integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_request_records_observability_started_and_completed() -> None:
    observability = MagicMock()

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter(FakeResearchBackend()))

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            observability=observability,
        )

        await engine.execute_request("Research JARVIS")

        observability.record_request_started.assert_called_once_with("Research JARVIS")
        observability.record_request_completed.assert_called_once_with(
            "Research JARVIS"
        )
        observability.record_request_failed.assert_not_called()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_records_observability_failed() -> None:
    observability = MagicMock()
    failing_execution_engine = MagicMock()
    failing_execution_engine.execute.side_effect = RuntimeError("execution failed")

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter())

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=failing_execution_engine,
            observability=observability,
        )

        with pytest.raises(RuntimeError):
            await engine.execute_request("Research JARVIS")

        observability.record_request_started.assert_called_once_with("Research JARVIS")
        observability.record_request_failed.assert_called_once_with("Research JARVIS")
        observability.record_request_completed.assert_not_called()
    finally:
        await store.close()


# ---------------------------------------------------------------------------
# Digital twin context
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_request_includes_digital_twin_snapshot() -> None:
    digital_twin = MagicMock()
    digital_twin.get_snapshot.return_value = {"os": "macOS"}

    context_engine = MagicMock()
    context_engine.build.return_value = MagicMock()

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter())

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=context_engine,
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            digital_twin=digital_twin,
        )

        await engine.execute_request(
            "Research JARVIS",
            context={"topic": "JARVIS"},
        )

        digital_twin.get_snapshot.assert_called_once()

        assert context_engine.build.call_args.kwargs["environment"] == {"os": "macOS"}
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_includes_real_digital_twin_snapshot() -> None:
    from kernel.environment.environment_snapshot import EnvironmentSnapshot

    digital_twin = DigitalTwin()
    digital_twin.update(EnvironmentSnapshot(cpu_usage=88.8))

    context_engine = MagicMock()
    context_engine.build.return_value = MagicMock()

    adapters = CapabilityAdapterManager()
    research = ResearchAdapter(FakeResearchBackend())
    await research.initialize()
    adapters.register(research)

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=context_engine,
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
            digital_twin=digital_twin,
        )

        await engine.execute_request(
            "Research JARVIS",
            context={"topic": "JARVIS"},
        )

        environment = context_engine.build.call_args.kwargs["environment"]
        assert environment["cpu_usage"] == 88.8
        assert "snapshot_id" in environment
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_without_digital_twin_preserves_context() -> None:
    context_engine = MagicMock()
    context_engine.build.return_value = MagicMock()

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter())

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=context_engine,
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        await engine.execute_request(
            "Research JARVIS",
            context={"topic": "JARVIS"},
        )

        assert context_engine.build.call_args.kwargs["environment"] is None
        assert context_engine.build.call_args.kwargs["user_input"] == "Research JARVIS"
    finally:
        await store.close()


# ---------------------------------------------------------------------------
# Context flow to execution
# ---------------------------------------------------------------------------


def make_capturing_adapters() -> tuple[MagicMock, list[CapabilityTask]]:
    """Provide a capability port that captures every dispatched task."""
    captured: list[CapabilityTask] = []
    adapters = MagicMock()
    adapters.can_handle.return_value = True
    adapters.execute = AsyncMock(
        side_effect=lambda task: (
            captured.append(task)
            or CapabilityResult(success=True, data={"intent": task.intent})
        )
    )
    return adapters, captured


@pytest.mark.asyncio
async def test_execute_request_context_reaches_capability_task() -> None:
    """Regression: the Context built by ContextEngine must reach the
    CapabilityTask populated with Context-derived data."""
    adapters, captured = make_capturing_adapters()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        await engine.execute_request(
            "Research JARVIS",
            context={
                "conversation_id": "conv-7",
                "session_id": "session-7",
                "working_memory": {"topic": "JARVIS"},
                "metadata": {"source": "cli"},
            },
        )

        task = captured[0]
        assert task.intent == "research"
        assert task.payload == {
            "user_input": "Research JARVIS",
            "working_memory": {"topic": "JARVIS"},
        }
        assert task.context["environment"] == {}
        assert task.metadata["conversation_id"] == "conv-7"
        assert task.metadata["session_id"] == "session-7"
        assert task.metadata["source"] == "cli"
        assert task.metadata["plan_id"].startswith("plan-")
        assert task.metadata["plan_action"] == "execute"
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_digital_twin_snapshot_survives_end_to_end() -> None:
    """Regression: the DigitalTwin snapshot must reach capability execution
    unchanged through the real pipeline."""
    from kernel.environment.environment_snapshot import EnvironmentSnapshot

    digital_twin = DigitalTwin()
    digital_twin.update(EnvironmentSnapshot(cpu_usage=88.8))

    adapters = CapabilityAdapterManager()
    research = ResearchAdapter(FakeResearchBackend())
    await research.initialize()
    adapters.register(research)

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
            digital_twin=digital_twin,
        )

        results = await engine.execute_request("Research JARVIS")

        task_context = results[0].metadata["capability_result"]["context"]
        assert task_context["environment"]["cpu_usage"] == 88.8
        assert "snapshot_id" in task_context["environment"]
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_working_memory_survives_end_to_end() -> None:
    """Regression: working memory must reach capability execution through
    the real pipeline."""
    adapters = CapabilityAdapterManager()
    research = ResearchAdapter(FakeResearchBackend())
    await research.initialize()
    adapters.register(research)

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        results = await engine.execute_request(
            "Research JARVIS",
            context={"working_memory": {"notes": "blue"}},
        )

        payload = results[0].metadata["capability_result"]["payload"]
        assert payload["user_input"] == "Research JARVIS"
        assert payload["working_memory"] == {"notes": "blue"}
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_conversation_session_survive_end_to_end() -> None:
    """Regression: conversation and session identifiers must reach the
    CapabilityTask metadata through the real pipeline."""
    adapters, captured = make_capturing_adapters()

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(capabilities=adapters),
        )

        await engine.execute_request(
            "Research JARVIS",
            context={
                "conversation_id": "conv-end-to-end",
                "session_id": "session-end-to-end",
            },
        )

        task = captured[0]
        assert task.metadata["conversation_id"] == "conv-end-to-end"
        assert task.metadata["session_id"] == "session-end-to-end"
    finally:
        await store.close()


# ---------------------------------------------------------------------------
# Engine introspection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_engine_exposes_intelligence_engines(
    executive_engine: ExecutiveEngine,
) -> None:
    assert isinstance(executive_engine.context_engine, ContextEngine)
    assert isinstance(executive_engine.intent_engine, IntentEngine)
    assert isinstance(executive_engine.reasoning_engine, ReasoningEngine)
    assert isinstance(executive_engine.decision_engine, DecisionEngine)
    assert isinstance(executive_engine.planning_engine, PlanningEngine)
    assert isinstance(executive_engine.execution_engine, ExecutionEngine)


@pytest.mark.asyncio
async def test_health_check_includes_intelligence_engines(
    executive_engine: ExecutiveEngine,
) -> None:
    health = await executive_engine.health_check()

    assert health["context_engine"] == {"healthy": True}
    assert health["intent_engine"] is True
    assert health["reasoning_engine"] is True
    assert health["decision_engine"] is True
    assert health["planning_engine"] == {"healthy": True}
    assert health["execution_engine"] == {"healthy": True}


@pytest.mark.asyncio
async def test_engine_info_reports_engines(executive_engine: ExecutiveEngine) -> None:
    info = await executive_engine.engine_info()

    assert isinstance(info["healthy"], bool)
    assert info["context_engine"] is True
    assert info["intent_engine"] is True
    assert info["reasoning_engine"] is True
    assert info["decision_engine"] is True
    assert info["planning_engine"] is True
    assert info["execution_engine"] is True
    assert info["plugins"] is False
    assert info["recovery"] is False


def test_capabilities_reports_intelligence_engines(
    executive_engine: ExecutiveEngine,
) -> None:
    capabilities = executive_engine.capabilities

    assert capabilities["context_engine"] is True
    assert capabilities["intent_engine"] is True
    assert capabilities["reasoning_engine"] is True
    assert capabilities["decision_engine"] is True
    assert capabilities["planning_engine"] is True
    assert capabilities["execution_engine"] is True
    assert capabilities["plugins"] is False
    assert capabilities["recovery"] is False


def test_is_observability_enabled_defaults_to_false(
    executive_engine: ExecutiveEngine,
) -> None:
    assert executive_engine.is_observability_enabled is False


# ---------------------------------------------------------------------------
# Security, recovery, workflows, and configuration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_denial_blocks_execution() -> None:
    security = MagicMock()
    security.authorize = AsyncMock(return_value=False)

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=security,
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine([]),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        with pytest.raises(PermissionError, match="Execution denied"):
            await engine.execute_capability("research", {})
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_security_denial_blocks_execution() -> None:
    security = MagicMock()
    security.authorize = AsyncMock(return_value=False)

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=security,
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        with pytest.raises(PermissionError, match="Execution denied"):
            await engine.execute_request("Research JARVIS")

        security.authorize.assert_awaited_once()
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_request_records_security_audit_entry(
    executive_engine: ExecutiveEngine,
) -> None:
    await executive_engine.execute_request("Research JARVIS")

    log = executive_engine.security.audit_log()

    assert len(log) == 1
    assert log[0]["event"] == "authorize"
    assert log[0]["details"] == {
        "subject": "executive_engine",
        "action": "research",
        "resource": "capability",
        "context": {},
        "allowed": True,
    }


@pytest.mark.asyncio
async def test_execute_capability_records_security_audit_entry(
    executive_engine: ExecutiveEngine,
) -> None:
    await executive_engine.execute_capability(
        "read_file",
        {"path": "README.md"},
    )

    log = executive_engine.security.audit_log()

    assert len(log) == 1
    assert log[0]["event"] == "authorize"
    assert log[0]["details"]["action"] == "read_file"
    assert log[0]["details"]["resource"] == "capability"
    assert log[0]["details"]["allowed"] is True


@pytest.mark.asyncio
async def test_both_execution_paths_enforce_identical_authorization(
    executive_engine: ExecutiveEngine,
) -> None:
    await executive_engine.execute_request("Research JARVIS")
    await executive_engine.execute_capability(
        "read_file",
        {"path": "README.md"},
    )

    log = executive_engine.security.audit_log()

    assert len(log) == 2
    assert [entry["event"] for entry in log] == ["authorize", "authorize"]
    assert [entry["details"]["action"] for entry in log] == [
        "research",
        "read_file",
    ]
    assert all(
        entry["details"]["subject"] == "executive_engine"
        and entry["details"]["resource"] == "capability"
        and entry["details"]["allowed"] is True
        for entry in log
    )


@pytest.mark.asyncio
async def test_execute_request_uses_recovery_when_configured() -> None:
    recovery = MagicMock()
    recovery.async_execute_with_recovery = AsyncMock(return_value=make_execution())

    adapters = CapabilityAdapterManager()
    adapters.register(ResearchAdapter())

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=WorkflowManager(),
            tools=ToolRegistry(),
            adapters=adapters,
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine(
                [
                    PolicyRule(intent="research", allowed=True),
                ]
            ),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
            recovery=recovery,
        )

        results = await engine.execute_request("Research JARVIS")

        recovery.async_execute_with_recovery.assert_awaited_once()
        assert results[0].success is True
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_execute_workflow() -> None:
    workflows = MagicMock()
    workflows.execute = AsyncMock(return_value={"done": True})

    store = SQLiteMemoryStore(":memory:")
    try:
        engine = ExecutiveEngine(
            memory=MemoryManager(store),
            workflows=workflows,
            tools=ToolRegistry(),
            adapters=CapabilityAdapterManager(),
            events=AsyncMock(),
            security=SecurityManager(),
            config=ConfigManager(),
            models=ModelManager(),
            policy=PolicyEngine([]),
            context_engine=ContextEngine(),
            intent_engine=IntentEngine(),
            reasoning_engine=ReasoningEngine(),
            decision_engine=DecisionEngine(),
            planning_engine=PlanningEngine(),
            execution_engine=ExecutionEngine(),
        )

        result = await engine.execute_workflow(
            "test.workflow",
            context={"key": "value"},
        )

        assert result == {"done": True}
        workflows.execute.assert_awaited_once_with(
            "test.workflow",
            context={"key": "value"},
        )
    finally:
        await store.close()


def test_config_property(executive_engine: ExecutiveEngine) -> None:
    assert isinstance(executive_engine.config, ConfigManager)
