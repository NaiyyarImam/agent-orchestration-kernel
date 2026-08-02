"""Metrics collection for the Kernel Observability Layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class Metric:
    """Represents a single named metric."""

    name: str
    value: float = 0.0

    def increment(self, amount: float = 1.0) -> None:
        """Increase the metric value."""
        self.value += amount

    def decrement(self, amount: float = 1.0) -> None:
        """Decrease the metric value."""
        self.value -= amount

    def set(self, value: float) -> None:
        """Assign a new value to the metric."""
        self.value = value

    def reset(self) -> None:
        """Reset the metric to zero."""
        self.value = 0.0

    def to_dict(self) -> dict[str, float]:
        """Serialize the metric."""
        return {
            "name": self.name,
            "value": self.value,
        }


class Metrics:
    """Registry and manager for kernel metrics."""

    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    @property
    def metrics(self) -> Mapping[str, Metric]:
        """Return a read-only view of registered metrics."""
        return self._metrics.copy()

    def register(self, name: str) -> Metric:
        """Register a metric if it does not already exist."""
        return self._metrics.setdefault(name, Metric(name=name))

    def get(self, name: str) -> Metric:
        """Return an existing metric."""
        return self._metrics[name]

    def increment(self, name: str, amount: float = 1.0) -> Metric:
        """Increment a metric."""
        metric = self.register(name)
        metric.increment(amount)
        return metric

    def decrement(self, name: str, amount: float = 1.0) -> Metric:
        """Decrement a metric."""
        metric = self.register(name)
        metric.decrement(amount)
        return metric

    def set(self, name: str, value: float) -> Metric:
        """Set a metric's value."""
        metric = self.register(name)
        metric.set(value)
        return metric

    def reset(self, name: str) -> None:
        """Reset a metric to zero."""
        self.get(name).reset()

    def clear(self) -> None:
        """Remove all registered metrics."""
        self._metrics.clear()

    def to_dict(self) -> dict[str, dict[str, float]]:
        """Serialize all metrics."""
        return {
            name: metric.to_dict()
            for name, metric in self._metrics.items()
        }