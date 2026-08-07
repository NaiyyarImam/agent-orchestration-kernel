"""Storage boundary used by capability adapters.

The contract expresses every filesystem operation capability adapters
are allowed to delegate. Concrete implementations (StorageManager) own
all filesystem logic; adapters must never perform filesystem work
themselves.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    """Safe filesystem access exposed to Kernel components."""

    @abstractmethod
    def path(self, *parts: str) -> Path:
        """Return a validated path below the configured storage root."""

    @abstractmethod
    def ensure_directory(self, *parts: str) -> Path:
        """Create a directory if it does not already exist."""

    @abstractmethod
    def write_text(self, relative_path: str, content: str) -> Path:
        """Write UTF-8 text to a file beneath the storage root."""

    @abstractmethod
    def read_text(self, relative_path: str) -> str:
        """Read UTF-8 text from a file beneath the storage root."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Return True if a file or directory exists."""

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Delete a file or directory. Return True if removed."""

    @abstractmethod
    def move(self, source: str, destination: str) -> Path:
        """Move a file or directory to a destination."""

    @abstractmethod
    def list(self, relative_path: str = "") -> list[Path]:
        """List entries beneath a directory."""
