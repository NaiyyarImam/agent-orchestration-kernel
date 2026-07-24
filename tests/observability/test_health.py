"""Unit tests for the Health Monitor."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.observability.health import (
    HealthCheck,
    HealthMonitor,
    HealthStatus,
)


def test_health_status_values() -> None:
    """HealthStatus should expose the expected values."""
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"


def test_health_check_defaults() -> None:
    """HealthCheck should initialize with sensible defaults."""
    check = HealthCheck(component="kernel")

    assert check.component == "kernel"
    assert check.status is HealthStatus.HEALTHY
    assert check.message == ""
    assert check.timestamp is not None


def test_health_check_is_healthy() -> None:
    """HealthCheck.is_healthy should reflect the status."""
    healthy = HealthCheck(
        component="kernel",
        status=HealthStatus.HEALTHY,
    )

    unhealthy = HealthCheck(
        component="kernel",
        status=HealthStatus.UNHEALTHY,
    )

    assert healthy.is_healthy() is True
    assert unhealthy.is_healthy() is False


def test_health_check_to_dict() -> None:
    """HealthCheck should serialize correctly."""
    check = HealthCheck(
        component="kernel",
        status=HealthStatus.DEGRADED,
        message="High memory usage",
    )

    data = check.to_dict()

    assert data["component"] == "kernel"
    assert data["status"] == "degraded"
    assert data["message"] == "High memory usage"
    assert isinstance(data["timestamp"], str)


def test_health_check_is_frozen() -> None:
    """HealthCheck should be immutable."""
    check = HealthCheck(component="kernel")

    with pytest.raises(FrozenInstanceError):
        check.component = "planner"  # type: ignore[misc]


def test_update_and_get() -> None:
    """HealthMonitor should update and retrieve checks."""
    monitor = HealthMonitor()

    check = monitor.update(
        "kernel",
        HealthStatus.DEGRADED,
        "Slow response",
    )

    assert monitor.get("kernel") is check


def test_overall_status_default() -> None:
    """An empty monitor should be healthy."""
    monitor = HealthMonitor()

    assert monitor.overall_status() is HealthStatus.HEALTHY


def test_overall_status_healthy() -> None:
    """Healthy checks should produce HEALTHY overall."""
    monitor = HealthMonitor()

    monitor.update("kernel")
    monitor.update("planner")

    assert monitor.overall_status() is HealthStatus.HEALTHY


def test_overall_status_degraded() -> None:
    """Any degraded component should produce DEGRADED overall."""
    monitor = HealthMonitor()

    monitor.update("kernel")
    monitor.update("planner", HealthStatus.DEGRADED)

    assert monitor.overall_status() is HealthStatus.DEGRADED


def test_overall_status_unhealthy() -> None:
    """Any unhealthy component should produce UNHEALTHY overall."""
    monitor = HealthMonitor()

    monitor.update("kernel", HealthStatus.DEGRADED)
    monitor.update("planner", HealthStatus.UNHEALTHY)

    assert monitor.overall_status() is HealthStatus.UNHEALTHY


def test_checks_property() -> None:
    """checks should return a copy of registered checks."""
    monitor = HealthMonitor()

    monitor.update("kernel")

    checks = monitor.checks

    assert "kernel" in checks
    assert checks is not monitor.checks


def test_clear() -> None:
    """clear should remove all health checks."""
    monitor = HealthMonitor()

    monitor.update("kernel")
    monitor.update("planner")

    monitor.clear()

    assert monitor.checks == {}


def test_monitor_to_dict() -> None:
    """HealthMonitor should serialize correctly."""
    monitor = HealthMonitor()

    monitor.update(
        "kernel",
        HealthStatus.HEALTHY,
        "OK",
    )

    data = monitor.to_dict()

    assert "kernel" in data
    assert data["kernel"]["status"] == "healthy"
    assert data["kernel"]["message"] == "OK"