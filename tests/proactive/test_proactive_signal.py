

"""Unit tests for the ProactiveSignal model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.proactive.proactive_signal import ProactiveSignal, SignalType


def test_signal_type_values() -> None:
    assert SignalType.SYSTEM.value == "system"
    assert SignalType.PERFORMANCE.value == "performance"
    assert SignalType.SECURITY.value == "security"
    assert SignalType.RESOURCE.value == "resource"
    assert SignalType.WORKFLOW.value == "workflow"
    assert SignalType.USER.value == "user"
    assert SignalType.CUSTOM.value == "custom"


def test_signal_defaults() -> None:
    signal = ProactiveSignal(
        source="kernel",
        signal_type=SignalType.SYSTEM,
        message="Kernel started",
    )

    assert signal.source == "kernel"
    assert signal.signal_type is SignalType.SYSTEM
    assert signal.message == "Kernel started"
    assert signal.confidence == 1.0
    assert signal.signal_id
    assert signal.metadata == {}


def test_custom_values() -> None:
    signal = ProactiveSignal(
        source="monitor",
        signal_type=SignalType.PERFORMANCE,
        message="High CPU usage",
        confidence=0.92,
        metadata={"cpu": 97},
    )

    assert signal.confidence == 0.92
    assert signal.metadata == {"cpu": 97}


def test_signal_is_frozen() -> None:
    signal = ProactiveSignal(
        source="kernel",
        signal_type=SignalType.SYSTEM,
        message="Started",
    )

    with pytest.raises(FrozenInstanceError):
        signal.message = "Changed"  # type: ignore[misc]


def test_to_dict() -> None:
    signal = ProactiveSignal(
        source="monitor",
        signal_type=SignalType.SECURITY,
        message="Suspicious login",
        confidence=0.85,
        metadata={"ip": "127.0.0.1"},
    )

    data = signal.to_dict()

    assert data["source"] == "monitor"
    assert data["signal_type"] == "security"
    assert data["message"] == "Suspicious login"
    assert data["confidence"] == 0.85
    assert data["metadata"] == {"ip": "127.0.0.1"}
    assert data["signal_id"] == signal.signal_id
    assert isinstance(data["timestamp"], str)