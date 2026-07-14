

"""Integration tests for Bootstrap."""

from __future__ import annotations

import pytest

from kernel.core.bootstrap import Bootstrap
from kernel.executive.executive_engine import ExecutiveEngine


@pytest.mark.asyncio
async def test_bootstrap_builds_engine() -> None:
    """Bootstrap should construct an ExecutiveEngine."""
    bootstrap = Bootstrap()

    engine = bootstrap.build()

    assert isinstance(engine, ExecutiveEngine)


def test_bootstrap_build_returns_engine_with_components() -> None:
    """Bootstrap should wire the core managers."""
    bootstrap = Bootstrap()

    engine = bootstrap.build()

    assert engine.memory is not None
    assert engine.models is not None
    assert engine.tools is not None
    assert engine.adapters is not None
    assert engine.workflows is not None
    assert engine.events is not None
    assert engine.security is not None


def test_bootstrap_default_model_registered() -> None:
    """Bootstrap should register at least one model provider."""
    bootstrap = Bootstrap()

    engine = bootstrap.build()

    provider = engine.models.default()

    assert provider is not None
    assert provider.name