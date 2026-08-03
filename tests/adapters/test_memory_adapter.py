"""Tests for the MemoryAdapter production implementation."""

from __future__ import annotations

import pytest
import pytest_asyncio

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.memory_adapter import MemoryAdapter
from kernel.core.bootstrap import Bootstrap
from kernel.interfaces.capability_adapter import CapabilityTask
from kernel.memory.memory_manager import MemoryManager
from kernel.policy import PolicyEngine, PolicyRule
from kernel.storage.sqlite_memory_store import SQLiteMemoryStore

MEMORY_POLICY_RULES = [
    PolicyRule(intent="remember", allowed=True),
    PolicyRule(intent="recall", allowed=True),
    PolicyRule(intent="search_memory", allowed=True),
    PolicyRule(intent="forget", allowed=True),
]


@pytest_asyncio.fixture
async def memory() -> MemoryManager:
    store = SQLiteMemoryStore(":memory:")
    manager = MemoryManager(store)
    try:
        yield manager
    finally:
        await store.close()


@pytest.fixture
def adapter(memory: MemoryManager) -> MemoryAdapter:
    return MemoryAdapter(memory)


class TestAdapterContract:
    """Tests for the MemoryAdapter contract (metadata, lifecycle, intents)."""

    def test_adapter_metadata(self) -> None:
        adapter = MemoryAdapter()
        assert adapter.name == "memory"
        assert adapter.capability_type == "memory"
        assert isinstance(adapter.description, str)
        assert adapter.description.strip() != ""

    @pytest.mark.asyncio
    async def test_initialize_and_health_check(self) -> None:
        adapter = MemoryAdapter()
        assert await adapter.health_check() is False
        await adapter.initialize()
        assert await adapter.health_check() is True

    @pytest.mark.parametrize(
        "intent",
        ["remember", "recall", "search_memory", "forget"],
    )
    def test_supported_intents(self, intent: str) -> None:
        adapter = MemoryAdapter()
        assert adapter.supports(intent) is True

    def test_unsupported_intent(self) -> None:
        adapter = MemoryAdapter()
        assert adapter.supports("unsupported") is False

    @pytest.mark.asyncio
    async def test_execute_requires_initialize(self) -> None:
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
    async def test_unsupported_intent_raises(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        with pytest.raises(ValueError):
            await adapter.execute(
                CapabilityTask(task_id="t", intent="research", payload={})
            )

    @pytest.mark.asyncio
    async def test_shutdown(self) -> None:
        adapter = MemoryAdapter()
        await adapter.initialize()
        await adapter.shutdown()
        assert await adapter.health_check() is False


class TestRemember:
    @pytest.mark.asyncio
    async def test_remember_stores_memory(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="remember",
                payload={"key": "color", "value": "blue"},
            )
        )
        assert result.success is True
        assert result.data["key"] == "color"
        assert result.data["status"] == "stored"
        assert result.metadata["adapter"] == "memory"
        assert result.metadata["status"] == "ok"
        assert await memory.load("color") == "blue"

    @pytest.mark.asyncio
    async def test_remember_without_key_derives_key(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="remember", payload={"text": "fact"})
        )
        assert result.success is True
        assert result.data["key"]
        assert await memory.load(result.data["key"]) == "fact"

    @pytest.mark.asyncio
    async def test_remember_missing_value(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="remember", payload={})
        )
        assert result.success is False
        assert "Missing 'value'" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_remember_manager_exception_becomes_failed_result(
        self, adapter: MemoryAdapter, memory: MemoryManager, monkeypatch
    ) -> None:
        async def explode(*args, **kwargs):
            raise RuntimeError("store exploded")

        monkeypatch.setattr(memory, "save", explode)
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="remember",
                payload={"key": "k", "value": "v"},
            )
        )
        assert result.success is False
        assert "Memory operation failed" in result.error
        assert "store exploded" in result.error


class TestRecall:
    @pytest.mark.asyncio
    async def test_recall_returns_stored_memory(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await memory.save("color", "blue")
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="recall", payload={"key": "color"})
        )
        assert result.success is True
        assert result.data["value"] == "blue"
        assert result.metadata["status"] == "ok"

    @pytest.mark.asyncio
    async def test_recall_missing_memory(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="recall", payload={"key": "ghost"})
        )
        assert result.success is False
        assert "Memory not found" in result.error

    @pytest.mark.asyncio
    async def test_recall_missing_key(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="recall", payload={})
        )
        assert result.success is False
        assert "Missing 'key'" in result.error


class TestSearchMemory:
    @pytest.mark.asyncio
    async def test_search_returns_matching_memories(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await memory.save("color", "my favorite color is blue")
        await memory.save("food", "I like pasta")
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t", intent="search_memory", payload={"query": "blue"}
            )
        )
        assert result.success is True
        assert result.data["results"] == ["my favorite color is blue"]
        assert result.metadata["status"] == "ok"

    @pytest.mark.asyncio
    async def test_search_no_results(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t", intent="search_memory", payload={"query": "zzz"}
            )
        )
        assert result.success is True
        assert result.data["results"] == []

    @pytest.mark.asyncio
    async def test_search_missing_query(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="search_memory", payload={})
        )
        assert result.success is False
        assert "Missing 'query'" in result.error

    @pytest.mark.asyncio
    async def test_search_honors_limit(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await memory.save("a", "match one")
        await memory.save("b", "match two")
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="search_memory",
                payload={"query": "match", "limit": 1},
            )
        )
        assert result.success is True
        assert len(result.data["results"]) == 1


class TestForget:
    @pytest.mark.asyncio
    async def test_forget_deletes_memory(
        self, adapter: MemoryAdapter, memory: MemoryManager
    ) -> None:
        await memory.save("temp", "data")
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="forget", payload={"key": "temp"})
        )
        assert result.success is True
        assert result.data["status"] == "forgotten"
        assert await memory.exists("temp") is False

    @pytest.mark.asyncio
    async def test_forget_missing_memory(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="forget", payload={"key": "ghost"})
        )
        assert result.success is False
        assert "Memory not found" in result.error

    @pytest.mark.asyncio
    async def test_forget_missing_key(self, adapter: MemoryAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="forget", payload={})
        )
        assert result.success is False
        assert "Missing 'key'" in result.error


class TestMemoryManagerNotConfigured:
    @pytest.mark.asyncio
    async def test_execute_without_manager_returns_failed_result(self) -> None:
        adapter = MemoryAdapter()
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="remember", payload={"value": "v"})
        )
        assert result.success is False
        assert "Memory manager is not configured" in result.error


class TestMemoryEndToEnd:
    """End-to-end dispatch through the CapabilityAdapterManager."""

    @pytest.fixture
    def manager(self, memory: MemoryManager) -> CapabilityAdapterManager:
        manager = CapabilityAdapterManager()
        manager.register(MemoryAdapter(memory))
        return manager

    @pytest.mark.asyncio
    async def test_remember_recall_search_forget_through_manager(
        self, manager: CapabilityAdapterManager, memory: MemoryManager
    ) -> None:
        await manager.initialize_all()

        remembered = await manager.execute(
            CapabilityTask(
                task_id="t1",
                intent="remember",
                payload={"key": "fact", "value": "the sky is blue"},
            )
        )
        assert remembered.success is True
        assert await memory.load("fact") == "the sky is blue"

        recalled = await manager.execute(
            CapabilityTask(task_id="t2", intent="recall", payload={"key": "fact"})
        )
        assert recalled.success is True
        assert recalled.data["value"] == "the sky is blue"

        searched = await manager.execute(
            CapabilityTask(
                task_id="t3", intent="search_memory", payload={"query": "blue"}
            )
        )
        assert searched.success is True
        assert "the sky is blue" in searched.data["results"]

        forgotten = await manager.execute(
            CapabilityTask(task_id="t4", intent="forget", payload={"key": "fact"})
        )
        assert forgotten.success is True
        assert await memory.exists("fact") is False


class TestMemoryThroughExecutiveEngine:
    """End-to-end execution through the composed Kernel ExecutiveEngine."""

    @pytest.mark.asyncio
    async def test_memory_operations_execute_through_kernel(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        bootstrap = Bootstrap()
        policy = PolicyEngine(list(MEMORY_POLICY_RULES))
        engine = bootstrap.build(policy=policy)
        try:
            await engine.adapters.initialize_all()

            remembered = await engine.execute_capability(
                "remember",
                {"key": "e2e_color", "value": "blue"},
            )
            assert remembered.success is True
            assert remembered.metadata["adapter"] == "memory"
            assert await engine.memory.load("e2e_color") == "blue"

            recalled = await engine.execute_capability(
                "recall",
                {"key": "e2e_color"},
            )
            assert recalled.success is True
            assert recalled.data["value"] == "blue"

            searched = await engine.execute_capability(
                "search_memory",
                {"query": "blue"},
            )
            assert searched.success is True
            assert "blue" in searched.data["results"]

            forgotten = await engine.execute_capability(
                "forget",
                {"key": "e2e_color"},
            )
            assert forgotten.success is True
            assert await engine.memory.exists("e2e_color") is False
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_remember_request_flows_through_full_pipeline(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        bootstrap = Bootstrap()
        policy = PolicyEngine(list(MEMORY_POLICY_RULES))
        engine = bootstrap.build(policy=policy)
        try:
            await engine.adapters.initialize_all()

            results = await engine.execute_request("Remember my favorite color is blue")
            assert results[0].success is True
            assert results[0].metadata["capability"] == "remember"
            assert results[0].metadata["adapter"] == "memory"

            matches = await engine.memory.search("blue")
            assert any(isinstance(value, str) and "blue" in value for value in matches)
        finally:
            await engine.memory.store.close()
