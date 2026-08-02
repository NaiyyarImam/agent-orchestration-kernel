"""Storage boundary used by capability adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    """Safe filesystem access exposed to Kernel components."""

    @abstractmethod
    def path(self, *parts: str) -> Path:
        """Return a validated path below the configured storage root."""
