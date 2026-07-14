

"""Integration tests for the Kernel lifecycle."""

from __future__ import annotations

import pytest

from kernel.core.kernel import Kernel


@pytest.mark.asyncio
async def test_kernel_initializes() -> None:
    """Kernel instance can be created."""
    kernel = Kernel()
    assert kernel is not None


@pytest.mark.asyncio
async def test_kernel_start_and_shutdown() -> None:
    """Kernel should start and shut down successfully."""
    kernel = Kernel()

    await kernel.start()
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_kernel_health_check() -> None:
    """Health check should return component status after startup."""
    kernel = Kernel()

    await kernel.start()

    health = await kernel.health_check()

    assert isinstance(health, dict)
    assert "memory" in health
    assert "models" in health
    assert "tools" in health
    assert "adapters" in health
    assert "workflows" in health
    assert "events" in health
    assert "security" in health

    await kernel.shutdown()


@pytest.mark.asyncio
async def test_kernel_multiple_start_shutdown_cycles() -> None:
    """Kernel should survive repeated lifecycle operations."""
    kernel = Kernel()

    await kernel.start()
    await kernel.shutdown()

    await kernel.start()
    await kernel.shutdown()