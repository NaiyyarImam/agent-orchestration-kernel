"""Unit tests for WorkflowManager."""

from __future__ import annotations

import pytest

from kernel.workflow.workflow_manager import WorkflowManager


@pytest.fixture
def manager() -> WorkflowManager:
    return WorkflowManager()


@pytest.fixture
def sample_workflow():
    async def workflow(context: dict):
        return {"ok": True, **context}
    return workflow


@pytest.mark.asyncio
async def test_register_and_list_workflow(manager: WorkflowManager, sample_workflow) -> None:
    await manager.register_workflow("analysis", sample_workflow)

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


@pytest.mark.asyncio
async def test_execute_non_callable_workflow(manager: WorkflowManager) -> None:
    """Test executing a workflow that is not callable (returns the workflow itself)."""
    await manager.register_workflow("static", {"result": "static"})

    result = await manager.execute("static")

    assert result == {"result": "static"}


@pytest.mark.asyncio
async def test_execute_workflow_failure(manager: WorkflowManager) -> None:
    """Test that workflow failure is recorded in history."""
    async def failing_workflow(context: dict):
        raise ValueError("workflow failed")

    await manager.register_workflow("failing", failing_workflow)

    with pytest.raises(ValueError, match="workflow failed"):
        await manager.execute("failing")

    history = await manager.workflow_history()
    assert len(history) == 1
    assert history[0]["status"] == "failed"
    assert history[0]["name"] == "failing"
    assert history[0]["failed_at"] is not None


@pytest.mark.asyncio
async def test_cancel_nonexistent_workflow_returns_false(manager: WorkflowManager) -> None:
    """Test cancelling a non-existent workflow returns False."""
    result = await manager.cancel("non-existent-id")
    assert result is False


@pytest.mark.asyncio
async def test_cancel_workflow_moves_to_history(manager: WorkflowManager) -> None:
    """Test that cancelled workflow is moved to history."""
    workflow_id = "test-workflow-id"
    manager._running[workflow_id] = {
        "id": workflow_id,
        "name": "test",
        "status": "running",
        "started_at": None,
        "completed_at": None,
        "failed_at": None,
        "cancelled_at": None,
    }

    result = await manager.cancel(workflow_id)

    assert result is True
    assert workflow_id not in manager._running
    assert workflow_id in manager._history
    assert manager._history[workflow_id]["status"] == "cancelled"
    assert manager._history[workflow_id]["cancelled_at"] is not None


@pytest.mark.asyncio
async def test_status_running_workflow(manager: WorkflowManager) -> None:
    """Test status for a running workflow."""
    workflow_id = "running-id"
    manager._running[workflow_id] = {
        "id": workflow_id,
        "name": "test",
        "status": "running",
    }

    status = await manager.status(workflow_id)

    assert status["id"] == workflow_id
    assert status["status"] == "running"


@pytest.mark.asyncio
async def test_status_completed_workflow(manager: WorkflowManager, sample_workflow) -> None:
    """Test status for a completed workflow."""
    await manager.register_workflow("test", sample_workflow)
    await manager.execute("test", context={"value": 1})

    history = await manager.workflow_history()
    workflow_id = history[0]["id"]

    status = await manager.status(workflow_id)

    assert status["id"] == workflow_id
    assert status["status"] == "completed"


@pytest.mark.asyncio
async def test_status_unknown_workflow(manager: WorkflowManager) -> None:
    """Test status for an unknown workflow returns unknown."""
    status = await manager.status("unknown-id")

    assert status == {"status": "unknown"}


@pytest.mark.asyncio
async def test_is_running_true(manager: WorkflowManager) -> None:
    """Test is_running returns True for running workflow."""
    workflow_id = "running-id"
    manager._running[workflow_id] = {
        "id": workflow_id,
        "name": "test",
        "status": "running",
    }

    result = await manager.is_running(workflow_id)

    assert result is True


@pytest.mark.asyncio
async def test_is_running_false(manager: WorkflowManager, sample_workflow) -> None:
    """Test is_running returns False for completed workflow."""
    await manager.register_workflow("test", sample_workflow)
    await manager.execute("test")

    history = await manager.workflow_history()
    workflow_id = history[0]["id"]

    result = await manager.is_running(workflow_id)

    assert result is False


@pytest.mark.asyncio
async def test_is_running_unknown(manager: WorkflowManager) -> None:
    """Test is_running returns False for unknown workflow."""
    result = await manager.is_running("unknown-id")

    assert result is False


@pytest.mark.asyncio
async def test_completed_workflows_includes_failed_and_cancelled(manager: WorkflowManager) -> None:
    """Test completed_workflows includes failed and cancelled workflows."""
    manager._history["failed-id"] = {
        "id": "failed-id",
        "name": "failed",
        "status": "failed",
        "failed_at": None,
    }
    manager._history["cancelled-id"] = {
        "id": "cancelled-id",
        "name": "cancelled",
        "status": "cancelled",
        "cancelled_at": None,
    }
    manager._running["running-id"] = {
        "id": "running-id",
        "name": "running",
        "status": "running",
    }

    completed = await manager.completed_workflows()

    assert len(completed) == 2
    statuses = {w["status"] for w in completed}
    assert statuses == {"failed", "cancelled"}


@pytest.mark.asyncio
async def test_running_workflows_returns_running(manager: WorkflowManager) -> None:
    """Test running_workflows returns currently running workflows."""
    manager._running["running-id"] = {
        "id": "running-id",
        "name": "test",
        "status": "running",
    }

    running = await manager.running_workflows()

    assert len(running) == 1
    assert running[0]["id"] == "running-id"


@pytest.mark.asyncio
async def test_workflow_count(manager: WorkflowManager, sample_workflow) -> None:
    """Test workflow_count returns correct count."""
    assert await manager.workflow_count() == 0

    await manager.register_workflow("workflow1", sample_workflow)
    assert await manager.workflow_count() == 1

    await manager.register_workflow("workflow2", sample_workflow)
    assert await manager.workflow_count() == 2


@pytest.mark.asyncio
async def test_workflow_info(manager: WorkflowManager, sample_workflow) -> None:
    """Test workflow_info returns correct metadata."""
    await manager.register_workflow("test", sample_workflow)
    await manager.execute("test")

    info = await manager.workflow_info()

    assert info["registered_workflows"] == 1
    assert info["running_workflows"] == 0
    assert info["completed_workflows"] == 1


@pytest.mark.asyncio
async def test_running_workflow_count(manager: WorkflowManager) -> None:
    """Test running_workflow_count returns correct count."""
    assert await manager.running_workflow_count() == 0

    manager._running["id1"] = {"status": "running"}
    assert await manager.running_workflow_count() == 1

    manager._running["id2"] = {"status": "running"}
    assert await manager.running_workflow_count() == 2


@pytest.mark.asyncio
async def test_manager_info(manager: WorkflowManager, sample_workflow) -> None:
    """Test manager_info returns correct information."""
    await manager.register_workflow("test", sample_workflow)
    await manager.execute("test")

    info = await manager.manager_info()

    assert info["healthy"] is True
    assert info["registered_workflows"] == 1
    assert info["running_workflows"] == 0