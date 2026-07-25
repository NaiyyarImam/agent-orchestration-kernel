"""Unit tests for the Metrics registry."""

from __future__ import annotations

from kernel.observability.metrics import Metric, Metrics


def test_metric_defaults() -> None:
    """Metric should initialize with default values."""
    metric = Metric(name="requests")

    assert metric.name == "requests"
    assert metric.value == 0.0


def test_metric_increment() -> None:
    """Metric.increment should increase the value."""
    metric = Metric(name="requests")

    metric.increment()
    metric.increment(4)

    assert metric.value == 5.0


def test_metric_decrement() -> None:
    """Metric.decrement should decrease the value."""
    metric = Metric(name="requests", value=10)

    metric.decrement()
    metric.decrement(2)

    assert metric.value == 7.0


def test_metric_set() -> None:
    """Metric.set should assign a value."""
    metric = Metric(name="requests")

    metric.set(42)

    assert metric.value == 42


def test_metric_reset() -> None:
    """Metric.reset should restore zero."""
    metric = Metric(name="requests", value=99)

    metric.reset()

    assert metric.value == 0.0


def test_metric_to_dict() -> None:
    """Metric should serialize correctly."""
    metric = Metric(name="requests", value=12)

    assert metric.to_dict() == {
        "name": "requests",
        "value": 12,
    }


def test_register_metric() -> None:
    """Registering a metric should create it once."""
    metrics = Metrics()

    metric = metrics.register("requests")

    assert metric.name == "requests"
    assert metric.value == 0.0
    assert metrics.register("requests") is metric


def test_get_metric() -> None:
    """Existing metrics should be retrievable."""
    metrics = Metrics()

    metric = metrics.register("requests")

    assert metrics.get("requests") is metric


def test_increment_metric() -> None:
    """Metrics.increment should register and increment."""
    metrics = Metrics()

    metric = metrics.increment("requests")

    assert metric.value == 1.0

    metrics.increment("requests", 4)

    assert metric.value == 5.0


def test_decrement_metric() -> None:
    """Metrics.decrement should decrease the value."""
    metrics = Metrics()

    metrics.set("requests", 10)

    metric = metrics.decrement("requests", 3)

    assert metric.value == 7.0


def test_set_metric() -> None:
    """Metrics.set should assign a value."""
    metrics = Metrics()

    metric = metrics.set("requests", 15)

    assert metric.value == 15


def test_reset_metric() -> None:
    """Metrics.reset should restore zero."""
    metrics = Metrics()

    metrics.set("requests", 22)
    metrics.reset("requests")

    assert metrics.get("requests").value == 0.0


def test_metrics_property() -> None:
    """metrics property should expose registered metrics."""
    metrics = Metrics()

    metrics.register("requests")
    metrics.register("errors")

    data = metrics.metrics

    assert set(data.keys()) == {"requests", "errors"}


def test_clear_metrics() -> None:
    """clear should remove all metrics."""
    metrics = Metrics()

    metrics.register("requests")
    metrics.register("errors")

    metrics.clear()

    assert metrics.metrics == {}


def test_metrics_to_dict() -> None:
    """Metrics should serialize correctly."""
    metrics = Metrics()

    metrics.set("requests", 3)
    metrics.set("errors", 1)

    assert metrics.to_dict() == {
        "requests": {
            "name": "requests",
            "value": 3,
        },
        "errors": {
            "name": "errors",
            "value": 1,
        },
    }