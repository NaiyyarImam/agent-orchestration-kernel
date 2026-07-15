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
from kernel.interfaces.capability_adapter import CapabilityResult
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

    engine = ExecutiveEngine(
        memory=memory,
        workflows=WorkflowManager(),
        tools=ToolRegistry(),
        adapters=adapters,
        events=events,
        security=SecurityManager(),
        config=config,
        models=models,
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


@pytest.mark.asyncio
async def test_execute_unknown_capability_raises(executive_engine: ExecutiveEngine) -> None:
    with pytest.raises(KeyError):
        await executive_engine.execute_capability(
            "does-not-exist",
            {},
        )