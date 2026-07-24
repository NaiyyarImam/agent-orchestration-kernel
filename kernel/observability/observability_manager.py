

"""Unified observability manager for the Kernel."""

from __future__ import annotations

from typing import Any

from kernel.observability.health import HealthMonitor, HealthStatus
from kernel.observability.logger import Logger
from kernel.observability.metrics import Metrics
from kernel.observability.tracer import TraceSpan, Tracer


class ObservabilityManager:
    """Coordinates logging, metrics, health, and tracing."""

    def __init__(self) -> None:
        self.logger = Logger()
        self.metrics = Metrics()
        self.health = HealthMonitor()
        self.tracer = Tracer()

    def log(self, level: str, message: str, **metadata: Any) -> None:
        """Record a log entry."""
        self.logger.log(level, message, **metadata)

    def increment_metric(self, name: str, amount: float = 1.0) -> None:
        """Increment a metric."""
        self.metrics.increment(name, amount)

    def update_health(
        self,
        component: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        message: str = "",
    ) -> None:
        """Update a component's health."""
        self.health.update(component, status, message)

    def start_span(self, name: str, **metadata: Any) -> TraceSpan:
        """Start a tracing span."""
        return self.tracer.start_span(name, **metadata)

    def finish_span(self, span: TraceSpan) -> TraceSpan:
        """Finish a tracing span."""
        return self.tracer.finish_span(span)

    def clear(self) -> None:
        """Clear all observability state."""
        self.logger.clear()
        self.metrics.clear()
        self.health.clear()
        self.tracer.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot of the current observability state."""
        return {
            "logs": [record.to_dict() for record in self.logger.records],
            "metrics": self.metrics.to_dict(),
            "health": {
                "overall_status": self.health.overall_status().value,
                "checks": self.health.to_dict(),
            },
            "traces": self.tracer.to_dict(),
        }