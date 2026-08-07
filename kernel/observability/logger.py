

"""Structured logger for the Kernel Observability Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class LogRecord:
    """Represents a structured log entry."""

    level: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the log record."""
        return {
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class Logger:
    """Simple in-memory structured logger."""

    def __init__(self) -> None:
        self._records: list[LogRecord] = []

    @property
    def records(self) -> tuple[LogRecord, ...]:
        """Return all log records as an immutable sequence."""
        return tuple(self._records)

    def log(self, level: str, message: str, **metadata: Any) -> LogRecord:
        """Create and store a structured log record."""
        record = LogRecord(
            level=level.upper(),
            message=message,
            metadata=metadata,
        )
        self._records.append(record)
        return record

    def info(self, message: str, **metadata: Any) -> LogRecord:
        return self.log("INFO", message, **metadata)

    def warning(self, message: str, **metadata: Any) -> LogRecord:
        return self.log("WARNING", message, **metadata)

    def error(self, message: str, **metadata: Any) -> LogRecord:
        return self.log("ERROR", message, **metadata)

    def clear(self) -> None:
        """Remove all stored log records."""
        self._records.clear()