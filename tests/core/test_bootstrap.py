"""Integration tests for Bootstrap."""

from __future__ import annotations

import pytest

from kernel.core.bootstrap import Bootstrap
from kernel.environment.digital_twin import DigitalTwin
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.intelligence.context_engine import ContextEngine
from kernel.intelligence.decision_engine import DecisionEngine
from kernel.intelligence.execution_engine import ExecutionEngine
from kernel.intelligence.intent_engine import IntentEngine
from kernel.intelligence.planning_engine import PlanningEngine
from kernel.intelligence.reasoning_engine import ReasoningEngine
from kernel.policy import PolicyEngine
from kernel.recovery.recovery_manager import RecoveryManager


@pytest.mark.asyncio
async def test_bootstrap_builds_engine() -> None:
    """Bootstrap should construct an ExecutiveEngine."""
    bootstrap = Bootstrap()

    engine = bootstrap.build(policy=PolicyEngine())

    try:
        assert isinstance(engine, ExecutiveEngine)
    finally:
        await engine.memory.store.close()


@pytest.mark.asyncio
async def test_bootstrap_build_returns_engine_with_components() -> None:
    """Bootstrap should wire the core managers."""
    bootstrap = Bootstrap()

    engine = bootstrap.build(policy=PolicyEngine())

    try:
        assert engine.memory is not None
        assert engine.models is not None
        assert engine.tools is not None
        assert engine.adapters is not None
        assert engine.workflows is not None
        assert engine.events is not None
        assert engine.security is not None
    finally:
        await engine.memory.store.close()


@pytest.mark.asyncio
async def test_bootstrap_injects_intelligence_engines() -> None:
    """Bootstrap should inject every intelligence engine."""
    bootstrap = Bootstrap()

    engine = bootstrap.build(policy=PolicyEngine())

    try:
        assert isinstance(engine.context_engine, ContextEngine)
        assert isinstance(engine.intent_engine, IntentEngine)
        assert isinstance(engine.reasoning_engine, ReasoningEngine)
        assert isinstance(engine.decision_engine, DecisionEngine)
        assert isinstance(engine.planning_engine, PlanningEngine)
        assert isinstance(engine.execution_engine, ExecutionEngine)
    finally:
        await engine.memory.store.close()


@pytest.mark.asyncio
async def test_bootstrap_injects_optional_integrations() -> None:
    """Bootstrap should inject DigitalTwin and RecoveryManager."""
    bootstrap = Bootstrap()

    engine = bootstrap.build(policy=PolicyEngine())

    try:
        assert isinstance(engine.digital_twin, DigitalTwin)
        assert isinstance(engine.recovery, RecoveryManager)
    finally:
        await engine.memory.store.close()


@pytest.mark.asyncio
async def test_bootstrap_default_model_registered() -> None:
    """Bootstrap should register at least one model provider."""
    bootstrap = Bootstrap()

    engine = bootstrap.build(policy=PolicyEngine())

    try:
        provider = engine.models.default()

        assert provider is not None
        assert provider.name
    finally:
        await engine.memory.store.close()
