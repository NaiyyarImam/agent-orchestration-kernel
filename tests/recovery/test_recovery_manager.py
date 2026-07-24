"""Unit tests for RecoveryManager."""

from __future__ import annotations

import pytest

from kernel.recovery.recovery_action import RecoveryAction
from kernel.recovery.recovery_manager import RecoveryManager
from kernel.recovery.recovery_policy import RecoveryPolicy
from kernel.recovery.recovery_result import RecoveryResult


def test_default_policy_is_created() -> None:
    """RecoveryManager should create a default policy."""
    manager = RecoveryManager()

    assert isinstance(manager.policy, RecoveryPolicy)
    assert manager.policy == RecoveryPolicy()


def test_custom_policy_is_used() -> None:
    """RecoveryManager should preserve an injected policy."""
    policy = RecoveryPolicy(
        max_retries=5,
        default_action=RecoveryAction.FAILOVER,
    )

    manager = RecoveryManager(policy)

    assert manager.policy is policy


def test_recover_before_retry_limit() -> None:
    """Recovery should succeed before the retry limit."""
    manager = RecoveryManager()

    result = manager.recover(0, "retrying")

    assert isinstance(result, RecoveryResult)
    assert result.success is True
    assert result.action is RecoveryAction.RETRY
    assert result.message == "retrying"


def test_recover_after_retry_limit() -> None:
    """Recovery should abort after the retry limit."""
    manager = RecoveryManager()

    result = manager.recover(3, "giving up")

    assert result.success is False
    assert result.action is RecoveryAction.ABORT
    assert result.message == "giving up"


def test_custom_policy_controls_action() -> None:
    """Custom policies should determine the recovery action."""
    policy = RecoveryPolicy(default_action=RecoveryAction.FAILOVER)

    manager = RecoveryManager(policy)

    result = manager.recover(100)

    assert result.success is True
    assert result.action is RecoveryAction.FAILOVER


def test_message_is_preserved() -> None:
    """Recovery messages should be preserved."""
    manager = RecoveryManager()

    message = "temporary network failure"

    result = manager.recover(1, message)

    assert result.message == message


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Health check should report the manager as healthy."""
    manager = RecoveryManager()

    assert await manager.health_check() is True