"""Tests for the ExecutiveEngine capability execution pipeline."""

from __future__ import annotations

import pytest

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.adapters.coding_adapter import CodingAdapter
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


@pytest.mark.asyncio
async def test_execute_unknown_capability_raises(executive_engine: ExecutiveEngine) -> None:
    with pytest.raises(KeyError):
        await executive_engine.execute_capability(
            "does-not-exist",
            {},
        )