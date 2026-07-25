

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.environment.environment_snapshot import EnvironmentSnapshot


@dataclass(slots=True)
class EnvironmentState:
    """Maintains the latest immutable snapshot of the Kernel environment."""

    current_snapshot: EnvironmentSnapshot = field(default_factory=EnvironmentSnapshot)

    def update(self, snapshot: EnvironmentSnapshot) -> None:
        """Replace the current environment snapshot."""
        self.current_snapshot = snapshot

    def get_snapshot(self) -> EnvironmentSnapshot:
        """Return the current environment snapshot."""
        return self.current_snapshot