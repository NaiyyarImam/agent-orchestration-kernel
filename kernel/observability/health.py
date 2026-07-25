"""Health monitoring for the Kernel Observability Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Represents the health state of a component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """Represents the health of a single component."""

    component: str
    status: HealthStatus = HealthStatus.HEALTHY
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_healthy(self) -> bool:
        """Return True if the component is healthy."""
        return self.status is HealthStatus.HEALTHY

    def to_dict(self) -> dict[str, str]:
        """Serialize the health check."""
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthMonitor:
    """Tracks health information for kernel components."""

    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    @property
    def checks(self) -> dict[str, HealthCheck]:
        """Return a copy of the registered health checks."""
        return self._checks.copy()

    def update(
        self,
        component: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        message: str = "",
    ) -> HealthCheck:
        """Create or update a health check."""
        check = HealthCheck(
            component=component,
            status=status,
            message=message,
        )
        self._checks[component] = check
        return check

    def get(self, component: str) -> HealthCheck:
        """Return the health check for a component."""
        return self._checks[component]

    def overall_status(self) -> HealthStatus:
        """Return the overall system health."""
        if not self._checks:
            return HealthStatus.HEALTHY

        statuses = {check.status for check in self._checks.values()}

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def clear(self) -> None:
        """Remove all health checks."""
        self._checks.clear()

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Serialize all health checks."""
        return {
            component: check.to_dict()
            for component, check in self._checks.items()
        }