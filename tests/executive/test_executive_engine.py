"""Tests for the ExecutiveEngine capability execution pipeline."""

from __future__ import annotations

import pytest

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.adapters.coding_adapter import CodingAdapter
from kernel.adapters.browser_adapter import BrowserAdapter
from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.adapters.voice_adapter import VoiceAdapter
from kernel.adapters.memory_adapter import MemoryAdapter
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.policy import PolicyEngine, PolicyRule
from kernel.interfaces.capability_adapter import CapabilityResult
from kernel.planning.execution_step import ExecutionStep
from kernel.planning.task_plan import TaskPlan
from unittest.mock import AsyncMock
from kernel.memory.memory_manager import MemoryManager
from kernel.storage.sqlite_memory_store import SQLiteMemoryStore
from kernel.security.security_manager import SecurityManager
from kernel.tools.tool_registry import ToolRegistry
from kernel.workflow.workflow_manager import WorkflowManager
from kernel.config.config_manager import ConfigManager
from kernel.models.model_manager import ModelManager

import pytest_asyncio


@pytest_asyncio.fixture
async def executive_engine() -> ExecutiveEngine:
    adapters = CapabilityAdapterManager()
    research = ResearchAdapter()
    await research.initialize()
    adapters.register(research)

    coding = CodingAdapter()
    await coding.initialize()
    adapters.register(coding)

    browser = BrowserAdapter()
    await browser.initialize()
    adapters.register(browser)

    workspace = WorkspaceAdapter()
    await workspace.initialize()
    adapters.register(workspace)

    voice = VoiceAdapter()
    await voice.initialize()
    adapters.register(voice)

    memory_adapter = MemoryAdapter()
    await memory_adapter.initialize()
    adapters.register(memory_adapter)

    events = AsyncMock()

    store = SQLiteMemoryStore(":memory:")
    memory = MemoryManager(store)

    config = ConfigManager()
    models = ModelManager()

    policy = PolicyEngine([
        PolicyRule(intent="speech_to_text", allowed=True),
        PolicyRule(intent="remember", allowed=True),
        PolicyRule(intent="research", allowed=True),
        PolicyRule(intent="generate_code", allowed=True),
        PolicyRule(intent="web_search", allowed=True),
        PolicyRule(intent="read_file", allowed=True),
    ])

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
    )

    return engine

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


# Test for memory capability
@pytest.mark.asyncio
async def test_execute_memory_capability(
    executive_engine: ExecutiveEngine,
) -> None:
    result = await executive_engine.execute_capability(
        "remember",
        {"text": "Hello JARVIS"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.data["intent"] == "remember"
    assert result.data["payload"] == {"text": "Hello JARVIS"}
    assert result.data["message"] == "Remember placeholder."


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
    assert result.data["payload"] == {
        "prompt": "print('Hello, JARVIS')"
    }
    assert "Generated code" in result.data["message"]


# New test for browser capability
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
    assert result.data["message"] == "Web search placeholder."


# New test for workspace capability
@pytest.mark.asyncio
async def test_execute_workspace_capability(
    executive_engine: ExecutiveEngine,
) -> None:
    result = await executive_engine.execute_capability(
        "read_file",
        {"path": "README.md"},
    )

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "workspace"
    assert result.data["intent"] == "read_file"
    assert result.data["payload"] == {"path": "README.md"}
    assert result.data["message"] == "Read file placeholder."




# Test for executing a plan with steps
import pytest

@pytest.mark.asyncio
async def test_execute_plan(
    executive_engine: ExecutiveEngine,
) -> None:
    plan = TaskPlan(
        plan_id="plan-1",
        goal="Research JARVIS",
    )

    plan.add_step(
        ExecutionStep(
            step_id="step-1",
            adapter="research",
            intent="research",
            payload={"query": "JARVIS"},
            description="Research the requested goal.",
        )
    )

    results = await executive_engine.execute_plan(plan)

    assert isinstance(results, list)
    assert len(results) == 1

    result = results[0]

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "research"
    assert result.data["intent"] == "research"
    assert result.data["payload"] == {"query": "JARVIS"}


@pytest.mark.asyncio
async def test_execute_unknown_capability_raises(executive_engine: ExecutiveEngine) -> None:
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
async def test_policy_denied_blocks_execution(executive_engine: ExecutiveEngine) -> None:
    executive_engine.policy.register(
        PolicyRule(intent="blocked.intent", allowed=False, reason="Blocked by policy")
    )

    with pytest.raises(PermissionError, match="Blocked by policy"):
        await executive_engine.execute_capability("blocked.intent", {})


@pytest.mark.asyncio
async def test_policy_requires_approval_blocks_execution(executive_engine: ExecutiveEngine) -> None:
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


def test_policy_property_returns_engine_policy(executive_engine: ExecutiveEngine) -> None:
    assert isinstance(executive_engine.policy, PolicyEngine)