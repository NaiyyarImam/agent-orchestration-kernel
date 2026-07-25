

import pytest

from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.interfaces.capability_adapter import CapabilityResult, CapabilityTask


def test_adapter_metadata() -> None:
    adapter = WorkspaceAdapter()
    assert adapter.name == "workspace"
    assert adapter.capability_type == "workspace"
    assert "workspace" in adapter.description.lower()


@pytest.mark.asyncio
async def test_initialize_and_health_check() -> None:
    adapter = WorkspaceAdapter()
    assert await adapter.health_check() is False
    await adapter.initialize()
    assert await adapter.health_check() is True


def test_supported_intents() -> None:
    adapter = WorkspaceAdapter()
    for intent in (
        "read_file",
        "write_file",
        "list_directory",
        "create_directory",
        "delete_file",
        "move_file",
    ):
        assert adapter.supports(intent) is True


def test_unsupported_intent() -> None:
    adapter = WorkspaceAdapter()
    assert adapter.supports("research") is False


@pytest.mark.asyncio
async def test_execute_requires_initialize() -> None:
    adapter = WorkspaceAdapter()
    with pytest.raises(RuntimeError):
        await adapter.execute(
            CapabilityTask(task_id="workspace-test-0", intent="read_file", payload={})
        )


async def _execute(intent: str, payload: dict, message: str) -> None:
    adapter = WorkspaceAdapter()
    await adapter.initialize()
    result = await adapter.execute(
        CapabilityTask(task_id=f"workspace-{intent}", intent=intent, payload=payload)
    )
    assert isinstance(result, CapabilityResult)
    assert result.success is True
    assert result.metadata["adapter"] == "workspace"
    assert result.data["intent"] == intent
    assert result.data["payload"] == payload
    assert result.data["message"] == message


@pytest.mark.asyncio
async def test_read_file_execution() -> None:
    await _execute("read_file", {"path": "README.md"}, "Read file placeholder.")


@pytest.mark.asyncio
async def test_write_file_execution() -> None:
    await _execute("write_file", {"path": "README.md"}, "Write file placeholder.")


@pytest.mark.asyncio
async def test_list_directory_execution() -> None:
    await _execute("list_directory", {"path": "."}, "List directory placeholder.")


@pytest.mark.asyncio
async def test_create_directory_execution() -> None:
    await _execute("create_directory", {"path": "docs"}, "Create directory placeholder.")


@pytest.mark.asyncio
async def test_delete_file_execution() -> None:
    await _execute("delete_file", {"path": "temp.txt"}, "Delete file placeholder.")


@pytest.mark.asyncio
async def test_move_file_execution() -> None:
    await _execute(
        "move_file",
        {"source": "a.txt", "destination": "b.txt"},
        "Move file placeholder.",
    )


@pytest.mark.asyncio
async def test_shutdown() -> None:
    adapter = WorkspaceAdapter()
    await adapter.initialize()
    await adapter.shutdown()
    assert await adapter.health_check() is False