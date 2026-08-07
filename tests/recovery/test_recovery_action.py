

"""Unit tests for RecoveryAction."""

from __future__ import annotations

from kernel.recovery.recovery_action import RecoveryAction


EXPECTED_ACTIONS = {
    "RETRY": "retry",
    "RESTART": "restart",
    "FAILOVER": "failover",
    "SKIP": "skip",
    "ABORT": "abort",
    "IGNORE": "ignore",
}


def test_recovery_action_members() -> None:
    """All expected recovery actions should exist."""
    assert len(RecoveryAction) == len(EXPECTED_ACTIONS)
    for name in EXPECTED_ACTIONS:
        assert hasattr(RecoveryAction, name)


def test_recovery_action_values() -> None:
    """Each recovery action should expose the correct value."""
    for name, value in EXPECTED_ACTIONS.items():
        assert getattr(RecoveryAction, name).value == value


def test_recovery_action_string_conversion() -> None:
    """String conversion should return the enum value."""
    for action in RecoveryAction:
        assert str(action) == action.value


def test_recovery_action_lookup_by_value() -> None:
    """Enum lookup by value should return the matching member."""
    for name, value in EXPECTED_ACTIONS.items():
        assert RecoveryAction(value) is getattr(RecoveryAction, name)