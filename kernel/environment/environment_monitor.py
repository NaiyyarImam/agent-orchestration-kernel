

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.environment.environment_change import EnvironmentChange
from kernel.environment.environment_snapshot import EnvironmentSnapshot
from kernel.environment.environment_state import EnvironmentState


@dataclass(slots=True)
class EnvironmentMonitor:
    """Captures environment snapshots and tracks detected changes."""

    state: EnvironmentState = field(default_factory=EnvironmentState)
    changes: list[EnvironmentChange] = field(default_factory=list)

    def capture_snapshot(self, snapshot: EnvironmentSnapshot) -> EnvironmentSnapshot:
        """Store a new environment snapshot and return it."""
        self.state.update(snapshot)
        return snapshot

    def record_change(self, change: EnvironmentChange) -> None:
        """Record a detected environment change."""
        self.changes.append(change)

    def get_current_snapshot(self) -> EnvironmentSnapshot:
        """Return the latest environment snapshot."""
        return self.state.get_snapshot()

    def get_changes(self) -> list[EnvironmentChange]:
        """Return a shallow copy of recorded environment changes."""
        return list(self.changes)

    def clear_changes(self) -> None:
        """Remove all recorded environment changes."""
        self.changes.clear()