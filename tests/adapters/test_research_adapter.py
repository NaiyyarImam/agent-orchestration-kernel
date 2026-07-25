"""Tests for the ResearchAdapter."""

from __future__ import annotations

import pytest

from kernel.adapters.research_adapter import ResearchAdapter
from kernel.interfaces.capability_adapter import CapabilityTask, CapabilityResult


@pytest.mark.asyncio
async def test_adapter_metadata() -> None:
    adapter = ResearchAdapter()

    assert adapter.name == "research"
    assert adapter.capability_type == "research"
    assert adapter.description


@pytest.mark.asyncio
async def test_initialize_and_health_check() -> None:
    adapter = ResearchAdapter()

    assert await adapter.health_check() is False

    await adapter.initialize()

    assert await adapter.health_check() is True


@pytest.mark.asyncio
async def test_supported_intents() -> None:
    adapter = ResearchAdapter()

    for intent in ["research", "search", "analyze", "investigate", "summarize"]:
        assert adapter.supports(intent) is True


@pytest.mark.asyncio
async def test_unsupported_intent() -> None:
    adapter = ResearchAdapter()

    assert adapter.supports("coding") is False


@pytest.mark.asyncio
async def test_execute_requires_initialize() -> None:
    adapter = ResearchAdapter()

    with pytest.raises(RuntimeError):
        await adapter.execute(
            CapabilityTask(
                task_id="test-task-1",
                intent="research",
                payload={},
            )
        )


@pytest.mark.asyncio
async def test_execute_returns_capability_result() -> None:
    adapter = ResearchAdapter()
    await adapter.initialize()

    task = CapabilityTask(
        task_id="test-task-2",
        intent="research",
        payload={"query": "JARVIS"},
    )

    result = await adapter.execute(task)

    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "research"
    assert result.data["intent"] == "research"
    assert result.data["payload"] == {"query": "JARVIS"}
    assert result.data["context"] == {}
    assert "placeholder executed successfully" in result.data["message"]
    assert result.metadata["status"] == "placeholder"


@pytest.mark.asyncio
async def test_shutdown() -> None:
    adapter = ResearchAdapter()

    await adapter.initialize()
    assert await adapter.health_check() is True

    await adapter.shutdown()

    assert await adapter.health_check() is False