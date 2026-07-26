"""Unit tests for WorkflowManager."""

from __future__ import annotations

import pytest

from kernel.workflow.workflow_manager import WorkflowManager


@pytest.mark.asyncio
async def test_register_and_list_workflow() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow("analysis", workflow)

    workflows = await manager.list_workflows()

    assert workflows == ["analysis"]



@pytest.mark.asyncio
async def test_register_workflow_with_metadata() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow(
        "analysis",
        workflow,
        description="Repository analysis workflow",
        version="2.0.0",
        tags=["analysis", "repository"],
        author="kernel",
    )

    metadata = await manager.workflow_metadata("analysis")

    assert metadata["name"] == "analysis"
    assert metadata["description"] == "Repository analysis workflow"
    assert metadata["version"] == "2.0.0"
    assert metadata["tags"] == ["analysis", "repository"]
    assert metadata["author"] == "kernel"
    assert metadata["registered_at"] is not None


@pytest.mark.asyncio
async def test_register_workflow_metadata_defaults() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow("analysis", workflow)

    metadata = await manager.workflow_metadata("analysis")

    assert metadata["description"] is None
    assert metadata["version"] == "1.0.0"
    assert metadata["tags"] == []
    assert metadata["author"] is None
    assert metadata["registered_at"] is not None


@pytest.mark.asyncio
async def test_workflow_metadata_unknown_workflow_raises() -> None:
    manager = WorkflowManager()

    with pytest.raises(KeyError):
        await manager.workflow_metadata("does-not-exist")



@pytest.mark.asyncio
async def test_execute_registered_workflow() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return {"ok": True, **context}

    await manager.register_workflow("analysis", workflow)

    result = await manager.execute(
        "analysis",
        context={"value": 42},
    )

    assert result == {"ok": True, "value": 42}


@pytest.mark.asyncio
async def test_workflow_history_and_completed_workflows() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow("analysis", workflow)

    await manager.execute("analysis", context={"value": 1})

    history = await manager.workflow_history()
    completed = await manager.completed_workflows()

    assert len(history) == 1
    assert len(completed) == 1
    assert completed[0]["status"] == "completed"
    assert completed[0]["name"] == "analysis"


@pytest.mark.asyncio
async def test_clear_history() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow("analysis", workflow)
    await manager.execute("analysis")

    assert len(await manager.workflow_history()) == 1

    await manager.clear_history()

    assert await manager.workflow_history() == []


@pytest.mark.asyncio
async def test_running_workflows_empty_after_completion() -> None:
    manager = WorkflowManager()

    async def workflow(context: dict):
        return context

    await manager.register_workflow("analysis", workflow)
    await manager.execute("analysis")

    assert await manager.running_workflows() == []


@pytest.mark.asyncio
async def test_execute_unknown_workflow_raises() -> None:
    manager = WorkflowManager()

    with pytest.raises(KeyError):
        await manager.execute("does-not-exist")


@pytest.mark.asyncio
async def test_health_check() -> None:
    manager = WorkflowManager()

    assert await manager.health_check() is True