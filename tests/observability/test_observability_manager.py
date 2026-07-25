

"""Unit tests for the ObservabilityManager."""

from __future__ import annotations

from kernel.observability.health import HealthStatus
from kernel.observability.observability_manager import ObservabilityManager


def test_initialization() -> None:
    manager = ObservabilityManager()

    assert manager.logger is not None
    assert manager.metrics is not None
    assert manager.health is not None
    assert manager.tracer is not None


def test_log() -> None:
    manager = ObservabilityManager()

    manager.log("INFO", "Kernel started", component="kernel")

    assert len(manager.logger.records) == 1
    record = manager.logger.records[0]
    assert record.level == "INFO"
    assert record.message == "Kernel started"
    assert record.metadata == {"component": "kernel"}


def test_increment_metric() -> None:
    manager = ObservabilityManager()

    manager.increment_metric("requests")
    manager.increment_metric("requests", 2)

    assert manager.metrics.get("requests").value == 3.0


def test_update_health() -> None:
    manager = ObservabilityManager()

    manager.update_health(
        "kernel",
        HealthStatus.DEGRADED,
        "High CPU usage",
    )

    check = manager.health.get("kernel")

    assert check.status is HealthStatus.DEGRADED
    assert check.message == "High CPU usage"


def test_start_and_finish_span() -> None:
    manager = ObservabilityManager()

    span = manager.start_span("boot")
    completed = manager.finish_span(span)

    assert completed.end_time is not None
    assert len(manager.tracer.spans) == 1


def test_record_request_started() -> None:
    manager = ObservabilityManager()

    manager.record_request_started("research")

    assert len(manager.logger.records) == 1
    record = manager.logger.records[0]
    assert record.level == "INFO"
    assert record.message == "Request started"
    assert record.metadata == {"objective": "research"}
    assert manager.metrics.get("requests.started").value == 1.0


def test_record_request_completed() -> None:
    manager = ObservabilityManager()

    manager.record_request_completed("research")

    assert len(manager.logger.records) == 1
    record = manager.logger.records[0]
    assert record.level == "INFO"
    assert record.message == "Request completed"
    assert record.metadata == {"objective": "research"}
    assert manager.metrics.get("requests.completed").value == 1.0


def test_record_request_failed() -> None:
    manager = ObservabilityManager()

    manager.record_request_failed("research")

    assert len(manager.logger.records) == 1
    record = manager.logger.records[0]
    assert record.level == "ERROR"
    assert record.message == "Request failed"
    assert record.metadata == {"objective": "research"}
    assert manager.metrics.get("requests.failed").value == 1.0


def test_snapshot() -> None:
    manager = ObservabilityManager()

    manager.log("INFO", "Started")
    manager.increment_metric("requests")
    manager.update_health("kernel")

    span = manager.start_span("boot")
    manager.finish_span(span)

    snapshot = manager.snapshot()

    assert set(snapshot.keys()) == {
        "logs",
        "metrics",
        "health",
        "traces",
    }

    assert len(snapshot["logs"]) == 1
    assert snapshot["metrics"]["requests"]["value"] == 1.0
    assert snapshot["health"]["overall_status"] == "healthy"
    assert len(snapshot["traces"]) == 1


def test_clear() -> None:
    manager = ObservabilityManager()

    manager.log("INFO", "Started")
    manager.increment_metric("requests")
    manager.update_health("kernel")
    manager.start_span("boot")

    manager.clear()

    assert manager.logger.records == ()
    assert manager.metrics.metrics == {}
    assert manager.health.checks == {}
    assert manager.tracer.spans == ()