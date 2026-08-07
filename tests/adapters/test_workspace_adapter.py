"""Tests for the WorkspaceAdapter production implementation."""

from __future__ import annotations

import pytest

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.core.bootstrap import Bootstrap
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask
from kernel.policy import PolicyEngine, PolicyRule
from kernel.storage.storage_manager import StorageManager

WORKSPACE_POLICY_RULES = [
    PolicyRule(intent="workspace", allowed=True),
    PolicyRule(intent="read_file", allowed=True),
    PolicyRule(intent="write_file", allowed=True),
    PolicyRule(intent="list_directory", allowed=True),
    PolicyRule(intent="create_directory", allowed=True),
    PolicyRule(intent="delete_file", allowed=True),
    PolicyRule(intent="move_file", allowed=True),
]


class TestAdapterContract:
    """Tests for the WorkspaceAdapter contract (metadata, lifecycle, intents)."""

    @pytest.fixture
    def adapter(self) -> WorkspaceAdapter:
        return WorkspaceAdapter()

    def test_adapter_metadata(self, adapter: WorkspaceAdapter) -> None:
        assert adapter.name == "workspace"
        assert adapter.capability_type == "workspace"
        assert "workspace" in adapter.description.lower()

    @pytest.mark.asyncio
    async def test_initialize_and_health_check(self, adapter: WorkspaceAdapter) -> None:
        assert await adapter.health_check() is False
        await adapter.initialize()
        assert await adapter.health_check() is True

    @pytest.mark.asyncio
    async def test_shutdown(self, adapter: WorkspaceAdapter) -> None:
        await adapter.initialize()
        await adapter.shutdown()
        assert await adapter.health_check() is False

    def test_supported_intents(self, adapter: WorkspaceAdapter) -> None:
        for intent in (
            "workspace",
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "delete_file",
            "move_file",
        ):
            assert adapter.supports(intent) is True

    def test_unsupported_intent(self, adapter: WorkspaceAdapter) -> None:
        assert adapter.supports("research") is False

    @pytest.mark.asyncio
    async def test_execute_requires_initialization(
        self, adapter: WorkspaceAdapter
    ) -> None:
        with pytest.raises(RuntimeError):
            await adapter.execute(
                CapabilityTask(task_id="t", intent="read_file", payload={"path": "x"})
            )


async def _execute(
    adapter: WorkspaceAdapter, intent: str, payload: dict
) -> CapabilityResult:
    await adapter.initialize()
    return await adapter.execute(
        CapabilityTask(task_id=f"workspace-{intent}", intent=intent, payload=payload)
    )


class TestWorkspaceOperations:
    """Tests for the real workspace operations delegated to StorageManager."""

    @pytest.fixture
    def storage(self, tmp_path) -> StorageManager:
        return StorageManager(tmp_path)

    @pytest.fixture
    def adapter(self, storage: StorageManager) -> WorkspaceAdapter:
        return WorkspaceAdapter(storage)

    @pytest.mark.asyncio
    async def test_write_file_creates_file(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        result = await _execute(
            adapter, "write_file", {"path": "notes/hello.txt", "content": "Hello"}
        )
        assert result.success is True
        assert result.data["intent"] == "write_file"
        assert result.data["status"] == "written"
        assert result.metadata["adapter"] == "workspace"
        assert result.metadata["status"] == "ok"
        assert storage.read_text("notes/hello.txt") == "Hello"

    @pytest.mark.asyncio
    async def test_write_file_overwrites_existing(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        await _execute(adapter, "write_file", {"path": "a.txt", "content": "first"})
        result = await _execute(
            adapter, "write_file", {"path": "a.txt", "content": "second"}
        )
        assert result.success is True
        assert storage.read_text("a.txt") == "second"

    @pytest.mark.asyncio
    async def test_write_file_missing_path(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "write_file", {"content": "x"})
        assert result.success is False
        assert "Missing 'path'" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_write_file_missing_content(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "write_file", {"path": "a.txt"})
        assert result.success is False
        assert "Missing 'content'" in result.error

    @pytest.mark.asyncio
    async def test_read_file_success(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        storage.write_text("test.txt", "Hello, World!")
        result = await _execute(adapter, "read_file", {"path": "test.txt"})
        assert result.success is True
        assert result.data["content"] == "Hello, World!"
        assert result.metadata["status"] == "ok"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "read_file", {"path": "missing.txt"})
        assert result.success is False
        assert "File not found" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_read_file_missing_path(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "read_file", {})
        assert result.success is False
        assert "Missing 'path'" in result.error

    @pytest.mark.asyncio
    async def test_delete_file(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        storage.write_text("temp.txt", "data")
        result = await _execute(adapter, "delete_file", {"path": "temp.txt"})
        assert result.success is True
        assert result.data["status"] == "deleted"
        assert storage.exists("temp.txt") is False

    @pytest.mark.asyncio
    async def test_delete_file_missing_file(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "delete_file", {"path": "ghost.txt"})
        assert result.success is False
        assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_delete_file_missing_path(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(adapter, "delete_file", {})
        assert result.success is False
        assert "Missing 'path'" in result.error

    @pytest.mark.asyncio
    async def test_move_file(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        storage.write_text("a.txt", "data")
        result = await _execute(
            adapter,
            "move_file",
            {"source": "a.txt", "destination": "sub/b.txt"},
        )
        assert result.success is True
        assert result.data["status"] == "moved"
        assert storage.exists("a.txt") is False
        assert storage.read_text("sub/b.txt") == "data"

    @pytest.mark.asyncio
    async def test_move_file_missing_source_param(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "move_file", {})
        assert result.success is False
        assert "Missing 'source'" in result.error

    @pytest.mark.asyncio
    async def test_move_file_missing_source(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(
            adapter, "move_file", {"source": "ghost.txt", "destination": "b.txt"}
        )
        assert result.success is False
        assert "Failed to move file" in result.error

    @pytest.mark.asyncio
    async def test_move_file_missing_destination(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "move_file", {"source": "a.txt"})
        assert result.success is False
        assert "Missing 'destination'" in result.error

    @pytest.mark.asyncio
    async def test_create_directory(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        result = await _execute(adapter, "create_directory", {"path": "docs/guides"})
        assert result.success is True
        assert result.data["status"] == "created"
        assert storage.path("docs/guides").is_dir()

    @pytest.mark.asyncio
    async def test_create_directory_missing_path(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "create_directory", {})
        assert result.success is False
        assert "Missing 'path'" in result.error

    @pytest.mark.asyncio
    async def test_list_directory(
        self, adapter: WorkspaceAdapter, storage: StorageManager
    ) -> None:
        storage.write_text("one.txt", "1")
        storage.write_text("two.txt", "2")
        storage.ensure_directory("sub")
        result = await _execute(adapter, "list_directory", {})
        assert result.success is True
        assert set(result.data["entries"]) == {"one.txt", "two.txt", "sub"}

    @pytest.mark.asyncio
    async def test_list_directory_missing_directory(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "list_directory", {"path": "void"})
        assert result.success is True
        assert result.data["entries"] == []

    @pytest.mark.asyncio
    async def test_workspace_intent_reports_capability(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "workspace", {})
        assert result.success is True
        assert result.metadata["status"] == "ok"
        assert "read_file" in result.data["supported_intents"]

    @pytest.mark.asyncio
    async def test_invalid_path_rejected(self, adapter: WorkspaceAdapter) -> None:
        result = await _execute(
            adapter, "write_file", {"path": "../escape.txt", "content": "x"}
        )
        assert result.success is False
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_storage_exception_becomes_failed_result(
        self, adapter: WorkspaceAdapter, storage: StorageManager, monkeypatch
    ) -> None:
        def explode(*args, **kwargs):
            raise RuntimeError("backend exploded")

        monkeypatch.setattr(storage, "write_text", explode)
        result = await _execute(
            adapter, "write_file", {"path": "a.txt", "content": "x"}
        )
        assert result.success is False
        assert "Failed to write file" in result.error
        assert "backend exploded" in result.error

    @pytest.mark.asyncio
    async def test_storage_not_configured(self) -> None:
        adapter = WorkspaceAdapter()
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="write_file",
                payload={"path": "a.txt", "content": "x"},
            )
        )
        assert result.success is False
        assert "Storage is not configured" in result.error

    @pytest.mark.asyncio
    async def test_unsupported_intent_via_execute(
        self, adapter: WorkspaceAdapter
    ) -> None:
        result = await _execute(adapter, "research", {"query": "x"})
        assert result.success is False
        assert "not supported" in result.error


class TestFailurePaths:
    """Coverage of every workspace failure branch."""

    @pytest.fixture
    def storage(self, tmp_path) -> StorageManager:
        return StorageManager(tmp_path)

    @pytest.fixture
    def adapter(self, storage: StorageManager) -> WorkspaceAdapter:
        return WorkspaceAdapter(storage)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("intent", "payload", "message"),
        [
            ("read_file", {"path": "a.txt"}, "Failed to read file"),
            ("delete_file", {"path": "a.txt"}, "Failed to delete file"),
            (
                "move_file",
                {"source": "a.txt", "destination": "b.txt"},
                "Failed to move file",
            ),
            ("create_directory", {"path": "d"}, "Failed to create directory"),
            ("list_directory", {"path": "d"}, "Failed to list directory"),
        ],
    )
    async def test_storage_exception_converted_per_operation(
        self,
        adapter: WorkspaceAdapter,
        storage: StorageManager,
        monkeypatch,
        intent: str,
        payload: dict,
        message: str,
    ) -> None:
        def explode(*args, **kwargs):
            raise RuntimeError("backend exploded")

        target = {
            "read_file": "read_text",
            "delete_file": "delete",
            "move_file": "move",
            "create_directory": "ensure_directory",
            "list_directory": "list",
        }[intent]
        monkeypatch.setattr(storage, target, explode)
        result = await _execute(adapter, intent, payload)
        assert result.success is False
        assert message in result.error

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("intent", "payload"),
        [
            ("read_file", {"path": "a.txt"}),
            ("delete_file", {"path": "a.txt"}),
            ("move_file", {"source": "a.txt", "destination": "b.txt"}),
            ("create_directory", {"path": "d"}),
            ("list_directory", {}),
        ],
    )
    async def test_storage_not_configured_per_operation(
        self, intent: str, payload: dict
    ) -> None:
        adapter = WorkspaceAdapter()
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent=intent, payload=payload)
        )
        assert result.success is False
        assert "Storage is not configured" in result.error


class TestWorkspaceEndToEnd:
    """End-to-end dispatch through the CapabilityAdapterManager."""

    @pytest.fixture
    def manager(self, tmp_path) -> tuple[CapabilityAdapterManager, StorageManager]:
        storage = StorageManager(tmp_path)
        adapter = WorkspaceAdapter(storage)
        manager = CapabilityAdapterManager()
        manager.register(adapter)
        return manager, storage

    @pytest.mark.asyncio
    async def test_write_and_read_through_manager(
        self, manager: tuple[CapabilityAdapterManager, StorageManager]
    ) -> None:
        manager, storage = manager
        await manager.initialize_all()
        write = await manager.execute(
            CapabilityTask(
                task_id="t1",
                intent="write_file",
                payload={"path": "notes.txt", "content": "Kernel"},
            )
        )
        assert write.success is True
        assert storage.read_text("notes.txt") == "Kernel"

        read = await manager.execute(
            CapabilityTask(
                task_id="t2", intent="read_file", payload={"path": "notes.txt"}
            )
        )
        assert read.success is True
        assert read.data["content"] == "Kernel"

    @pytest.mark.asyncio
    async def test_delete_through_manager(
        self, manager: tuple[CapabilityAdapterManager, StorageManager]
    ) -> None:
        manager, storage = manager
        await manager.initialize_all()
        await manager.execute(
            CapabilityTask(
                task_id="t1",
                intent="write_file",
                payload={"path": "temp.txt", "content": "x"},
            )
        )
        result = await manager.execute(
            CapabilityTask(
                task_id="t2", intent="delete_file", payload={"path": "temp.txt"}
            )
        )
        assert result.success is True
        assert storage.exists("temp.txt") is False


class TestWorkspaceThroughExecutiveEngine:
    """End-to-end execution through the composed Kernel ExecutiveEngine."""

    @pytest.mark.asyncio
    async def test_workspace_operations_execute_through_kernel(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        bootstrap = Bootstrap()
        policy = PolicyEngine(list(WORKSPACE_POLICY_RULES))
        engine = bootstrap.build(policy=policy)
        try:
            await engine.adapters.initialize_all()

            write = await engine.execute_capability(
                "write_file",
                {"path": "kernel_e2e/notes.txt", "content": "Hello Kernel"},
            )
            assert write.success is True
            assert write.metadata["adapter"] == "workspace"

            storage = StorageManager(engine.config.storage.root)
            assert storage.read_text("kernel_e2e/notes.txt") == "Hello Kernel"

            read = await engine.execute_capability(
                "read_file",
                {"path": "kernel_e2e/notes.txt"},
            )
            assert read.success is True
            assert read.data["content"] == "Hello Kernel"

            moved = await engine.execute_capability(
                "move_file",
                {
                    "source": "kernel_e2e/notes.txt",
                    "destination": "kernel_e2e/moved.txt",
                },
            )
            assert moved.success is True
            assert storage.exists("kernel_e2e/notes.txt") is False

            deleted = await engine.execute_capability(
                "delete_file",
                {"path": "kernel_e2e/moved.txt"},
            )
            assert deleted.success is True
            assert storage.exists("kernel_e2e/moved.txt") is False
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_workspace_pipeline_requires_confirmation(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        bootstrap = Bootstrap()
        policy = PolicyEngine(list(WORKSPACE_POLICY_RULES))
        engine = bootstrap.build(policy=policy)
        try:
            await engine.adapters.initialize_all()
            results = await engine.execute_request("open my project")
            assert results[0].data["action"] == "request_confirmation"
            assert results[0].data["status"] == "PENDING"
        finally:
            await engine.memory.store.close()
