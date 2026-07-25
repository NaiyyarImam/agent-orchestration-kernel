

"""Unit tests for RecoveryPolicy."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.recovery.recovery_action import RecoveryAction
from kernel.recovery.recovery_policy import RecoveryPolicy


def test_recovery_policy_defaults() -> None:
    """RecoveryPolicy should expose sensible defaults."""
    policy = RecoveryPolicy()

    assert policy.max_retries == 3
    assert policy.default_action is RecoveryAction.RETRY
    assert policy.retry_delay_seconds == 0.0


def test_recovery_policy_custom_values() -> None:
    """RecoveryPolicy should preserve custom configuration."""
    policy = RecoveryPolicy(
        max_retries=5,
        default_action=RecoveryAction.RESTART,
        retry_delay_seconds=1.5,
    )

    assert policy.max_retries == 5
    assert policy.default_action is RecoveryAction.RESTART
    assert policy.retry_delay_seconds == 1.5


@pytest.mark.parametrize("retries", [-1, -10])
def test_invalid_max_retries(retries: int) -> None:
    """Negative retry counts should be rejected."""
    with pytest.raises(ValueError, match="max_retries"):
        RecoveryPolicy(max_retries=retries)


@pytest.mark.parametrize("delay", [-0.1, -5.0])
def test_invalid_retry_delay(delay: float) -> None:
    """Negative retry delays should be rejected."""
    with pytest.raises(ValueError, match="retry_delay_seconds"):
        RecoveryPolicy(retry_delay_seconds=delay)


def test_next_action_before_retry_limit() -> None:
    """Attempts below the retry limit should use the default action."""
    policy = RecoveryPolicy(max_retries=3)

    assert policy.next_action(0) is RecoveryAction.RETRY
    assert policy.next_action(2) is RecoveryAction.RETRY


def test_next_action_after_retry_limit() -> None:
    """Attempts at or beyond the retry limit should abort."""
    policy = RecoveryPolicy(max_retries=3)

    assert policy.next_action(3) is RecoveryAction.ABORT
    assert policy.next_action(10) is RecoveryAction.ABORT


def test_non_retry_default_action_is_preserved() -> None:
    """Policies using a non-RETRY default should always return that action."""
    policy = RecoveryPolicy(default_action=RecoveryAction.FAILOVER)

    assert policy.next_action(0) is RecoveryAction.FAILOVER
    assert policy.next_action(100) is RecoveryAction.FAILOVER


def test_negative_attempt_is_rejected() -> None:
    """Negative attempt numbers should raise ValueError."""
    policy = RecoveryPolicy()

    with pytest.raises(ValueError, match="attempt"):
        policy.next_action(-1)


def test_recovery_policy_is_frozen() -> None:
    """RecoveryPolicy should be immutable."""
    policy = RecoveryPolicy()

    with pytest.raises(FrozenInstanceError):
        policy.max_retries = 10  # type: ignore[misc]