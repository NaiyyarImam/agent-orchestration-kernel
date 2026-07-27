

import pytest

from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask
from kernel.storage.storage_manager import StorageManager


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


class TestReadFile:
    """Tests for the real read_file implementation."""

    @pytest.fixture
    def storage(self, tmp_path) -> StorageManager:
        return StorageManager(tmp_path)

    @pytest.fixture
    def adapter(self, storage) -> WorkspaceAdapter:
        return WorkspaceAdapter(storage)

    @pytest.mark.asyncio
    async def test_read_file_success(self, adapter: WorkspaceAdapter, storage: StorageManager, tmp_path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="read-1", intent="read_file", payload={"path": "test.txt"})
        )
        assert result.success is True
        assert result.data["content"] == "Hello, World!"
        assert result.metadata["adapter"] == "workspace"
        assert result.metadata["status"] == "ok"

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, adapter: WorkspaceAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="read-2", intent="read_file", payload={"path": "missing.txt"})
        )
        assert result.success is False
        assert "File not found" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_read_file_missing_path(self, adapter: WorkspaceAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="read-3", intent="read_file", payload={})
        )
        assert result.success is False
        assert "Missing 'path'" in result.error

    @pytest.mark.asyncio
    async def test_read_file_not_initialized(self, adapter: WorkspaceAdapter) -> None:
        with pytest.raises(RuntimeError):
            await adapter.execute(
                CapabilityTask(task_id="read-4", intent="read_file", payload={"path": "test.txt"})
            )


class TestPlaceholderIntents:
    """Ensure other intents still behave as placeholders."""

    @pytest.fixture
    def adapter(self) -> WorkspaceAdapter:
        return WorkspaceAdapter()

    async def _execute(self, adapter: WorkspaceAdapter, intent: str, payload: dict, message: str) -> CapabilityResult:
        await adapter.initialize()
        return await adapter.execute(
            CapabilityTask(task_id=f"workspace-{intent}", intent=intent, payload=payload)
        )

    @pytest.mark.asyncio
    async def test_write_file_placeholder(self, adapter: WorkspaceAdapter) -> None:
        result = await self._execute(adapter, "write_file", {"path": "README.md"}, "Write file placeholder.")
        assert result.success is True
        assert result.data["message"] == "Write file placeholder."
        assert result.metadata["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_list_directory_placeholder(self, adapter: WorkspaceAdapter) -> None:
        result = await self._execute(adapter, "list_directory", {"path": "."}, "List directory placeholder.")
        assert result.success is True
        assert result.data["message"] == "List directory placeholder."
        assert result.metadata["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_create_directory_placeholder(self, adapter: WorkspaceAdapter) -> None:
        result = await self._execute(adapter, "create_directory", {"path": "docs"}, "Create directory placeholder.")
        assert result.success is True
        assert result.data["message"] == "Create directory placeholder."
        assert result.metadata["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_delete_file_placeholder(self, adapter: WorkspaceAdapter) -> None:
        result = await self._execute(adapter, "delete_file", {"path": "temp.txt"}, "Delete file placeholder.")
        assert result.success is True
        assert result.data["message"] == "Delete file placeholder."
        assert result.metadata["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_move_file_placeholder(self, adapter: WorkspaceAdapter) -> None:
        result = await self._execute(
            adapter, "move_file", {"source": "a.txt", "destination": "b.txt"}, "Move file placeholder."
        )
        assert result.success is True
        assert result.data["message"] == "Move file placeholder."
        assert result.metadata["status"] == "placeholder"