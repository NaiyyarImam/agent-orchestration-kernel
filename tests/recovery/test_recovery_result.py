

"""Unit tests for RecoveryResult."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from kernel.recovery.recovery_action import RecoveryAction
from kernel.recovery.recovery_result import RecoveryResult


def test_recovery_result_defaults() -> None:
    """RecoveryResult should populate default fields."""
    result = RecoveryResult(success=True, action=RecoveryAction.RETRY)

    assert result.success is True
    assert result.action is RecoveryAction.RETRY
    assert result.message == ""
    assert isinstance(result.timestamp, datetime)


def test_recovery_result_custom_values() -> None:
    """RecoveryResult should preserve supplied values."""
    result = RecoveryResult(
        success=False,
        action=RecoveryAction.ABORT,
        message="Maximum retries exceeded",
    )

    assert result.success is False
    assert result.action is RecoveryAction.ABORT
    assert result.message == "Maximum retries exceeded"


def test_recovery_result_to_dict() -> None:
    """RecoveryResult should serialize correctly."""
    result = RecoveryResult(True, RecoveryAction.RESTART, "Recovered")

    data = result.to_dict()

    assert data["success"] is True
    assert data["action"] == "restart"
    assert data["message"] == "Recovered"
    assert isinstance(data["timestamp"], str)


def test_recovery_result_from_dict() -> None:
    """RecoveryResult should deserialize correctly."""
    original = RecoveryResult(False, RecoveryAction.FAILOVER, "Fallback used")

    restored = RecoveryResult.from_dict(original.to_dict())

    assert restored == original


def test_recovery_result_is_frozen() -> None:
    """RecoveryResult should be immutable."""
    result = RecoveryResult(True, RecoveryAction.IGNORE)

    with pytest.raises(FrozenInstanceError):
        result.message = "modified"  # type: ignore[misc]