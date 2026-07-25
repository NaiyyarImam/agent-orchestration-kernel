import pytest
from kernel.adapters.coding_adapter import CodingAdapter
from kernel.interfaces.capability_adapter import (
    CapabilityTask,
    CapabilityResult,
)


def test_adapter_metadata():
    adapter = CodingAdapter()
    assert adapter.name == "coding"
    assert adapter.capability_type == "coding"
    assert isinstance(adapter.description, str) and adapter.description.strip() != ""


@pytest.mark.asyncio
async def test_initialize_and_health_check():
    adapter = CodingAdapter()
    assert await adapter.health_check() is False
    await adapter.initialize()
    assert await adapter.health_check() is True


def test_supported_intents():
    adapter = CodingAdapter()
    supported = [
        "code",
        "coding",
        "generate_code",
        "explain_code",
        "review_code",
        "refactor_code",
        "debug_code",
        "test_code",
    ]
    for intent in supported:
        assert adapter.supports(intent) is True


def test_unsupported_intent():
    adapter = CodingAdapter()
    for intent in ["research", "browser"]:
        assert adapter.supports(intent) is False


@pytest.mark.asyncio
async def test_execute_requires_initialize():
    adapter = CodingAdapter()
    task = CapabilityTask(task_id="test-task-1", intent="generate_code", payload={})
    with pytest.raises(RuntimeError):
        await adapter.execute(task)


@pytest.mark.asyncio
async def test_generate_code_execution():
    adapter = CodingAdapter()
    await adapter.initialize()
    payload = {"prompt": "hello"}
    task = CapabilityTask(
        task_id="generate-1",
        intent="generate_code",
        payload=payload,
    )
    result = await adapter.execute(task)
    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata.get("adapter") == "coding"
    assert result.data.get("intent") == "generate_code"
    assert result.data.get("payload") == payload
    assert "Generated code" in result.data["message"]


@pytest.mark.asyncio
async def test_review_code_execution():
    adapter = CodingAdapter()
    await adapter.initialize()
    task = CapabilityTask(
        task_id="review-1",
        intent="review_code",
        payload={"code": "print('hi')"},
    )
    result = await adapter.execute(task)
    assert isinstance(result, CapabilityResult)
    assert "review" in result.data["message"].lower()


@pytest.mark.asyncio
async def test_debug_code_execution():
    adapter = CodingAdapter()
    await adapter.initialize()
    task = CapabilityTask(
        task_id="debug-1",
        intent="debug_code",
        payload={"code": "print(1/0)"},
    )
    result = await adapter.execute(task)
    assert isinstance(result, CapabilityResult)
    assert "debug" in result.data["message"].lower()


@pytest.mark.asyncio
async def test_shutdown():
    adapter = CodingAdapter()
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False