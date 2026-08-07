

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.environment.environment_change import EnvironmentChange
from kernel.environment.environment_monitor import EnvironmentMonitor
from kernel.environment.environment_snapshot import EnvironmentSnapshot


@dataclass(slots=True)
class DigitalTwin:
    """High-level façade for the Kernel's local environment model."""

    monitor: EnvironmentMonitor = field(default_factory=EnvironmentMonitor)

    def update(self, snapshot: EnvironmentSnapshot) -> EnvironmentSnapshot:
        """Update the digital twin with a new environment snapshot."""
        return self.monitor.capture_snapshot(snapshot)

    def record_change(self, change: EnvironmentChange) -> None:
        """Record an environment change."""
        self.monitor.record_change(change)

    def get_snapshot(self) -> EnvironmentSnapshot:
        """Return the latest environment snapshot."""
        return self.monitor.get_current_snapshot()

    def get_changes(self) -> list[EnvironmentChange]:
        """Return the recorded environment changes."""
        return self.monitor.get_changes()

    def clear_changes(self) -> None:
        """Clear all recorded environment changes."""
        self.monitor.clear_changes()