import pytest

from kernel.adapters.memory_adapter import MemoryAdapter
from kernel.interfaces.capability_adapter import CapabilityTask


@pytest.mark.asyncio
async def test_adapter_metadata():
    adapter = MemoryAdapter()
    assert adapter.name == "memory"
    assert adapter.capability_type == "memory"
    assert isinstance(adapter.description, str)
    assert adapter.description.strip() != ""


@pytest.mark.asyncio
async def test_initialize_and_health_check():
    adapter = MemoryAdapter()
    # Should not be healthy before initialize
    assert await adapter.health_check() is False
    await adapter.initialize()
    assert await adapter.health_check() is True


@pytest.mark.parametrize("intent", [
    "remember",
    "recall",
    "search_memory",
    "forget",
])
def test_supported_intents(intent):
    adapter = MemoryAdapter()
    assert adapter.supports(intent) is True


def test_unsupported_intent():
    adapter = MemoryAdapter()
    assert adapter.supports("unsupported") is False


@pytest.mark.asyncio
async def test_execute_requires_initialize():
    adapter = MemoryAdapter()
    task = CapabilityTask(
        task_id="test-task-id",
        intent="remember",
        payload={"text": "foo"},
        metadata={},
        context={},
    )
    with pytest.raises(RuntimeError):
        await adapter.execute(task)


@pytest.mark.asyncio
async def test_remember_execution():
    adapter = MemoryAdapter()
    await adapter.initialize()
    payload = {"text": "foo"}
    task = CapabilityTask(
        task_id="test-task-id",
        intent="remember",
        payload=payload,
        metadata={},
        context={},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.data["intent"] == "remember"
    assert result.data["payload"] == payload
    assert result.data["message"] == "Remember placeholder."


@pytest.mark.asyncio
async def test_recall_execution():
    adapter = MemoryAdapter()
    await adapter.initialize()
    payload = {"query": "bar"}
    task = CapabilityTask(
        task_id="test-task-id",
        intent="recall",
        payload=payload,
        metadata={},
        context={},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.data["intent"] == "recall"
    assert result.data["payload"] == payload
    assert result.data["message"] == "Recall placeholder."


@pytest.mark.asyncio
async def test_search_memory_execution():
    adapter = MemoryAdapter()
    await adapter.initialize()
    payload = {"query": "baz"}
    task = CapabilityTask(
        task_id="test-task-id",
        intent="search_memory",
        payload=payload,
        metadata={},
        context={},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.data["intent"] == "search_memory"
    assert result.data["payload"] == payload
    assert result.data["message"] == "Search memory placeholder."


@pytest.mark.asyncio
async def test_forget_execution():
    adapter = MemoryAdapter()
    await adapter.initialize()
    payload = {"text": "forget this"}
    task = CapabilityTask(
        task_id="test-task-id",
        intent="forget",
        payload=payload,
        metadata={},
        context={},
    )
    result = await adapter.execute(task)
    assert result.success is True
    assert result.metadata["adapter"] == "memory"
    assert result.data["intent"] == "forget"
    assert result.data["payload"] == payload
    assert result.data["message"] == "Forget placeholder."


@pytest.mark.asyncio
async def test_shutdown():
    adapter = MemoryAdapter()
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False