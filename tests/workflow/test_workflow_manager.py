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
async def test_execute_unknown_workflow_raises() -> None:
    manager = WorkflowManager()

    with pytest.raises(KeyError):
        await manager.execute("does-not-exist")


@pytest.mark.asyncio
async def test_health_check() -> None:
    manager = WorkflowManager()

    assert await manager.health_check() is True