"""Unit tests for the Logger."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from kernel.observability.logger import LogRecord, Logger


def test_log_record_defaults() -> None:
    """LogRecord should initialize with default values."""
    record = LogRecord(
        level="INFO",
        message="Kernel started",
    )

    assert record.level == "INFO"
    assert record.message == "Kernel started"
    assert record.metadata == {}
    assert record.timestamp is not None


def test_log_record_to_dict() -> None:
    """LogRecord should serialize correctly."""
    record = LogRecord(
        level="ERROR",
        message="Failure",
        metadata={"module": "kernel"},
    )

    data = record.to_dict()

    assert data["level"] == "ERROR"
    assert data["message"] == "Failure"
    assert data["metadata"] == {"module": "kernel"}
    assert isinstance(data["timestamp"], str)


def test_log_record_is_frozen() -> None:
    """LogRecord should be immutable."""
    record = LogRecord(
        level="INFO",
        message="Immutable",
    )

    with pytest.raises(FrozenInstanceError):
        record.level = "ERROR"  # type: ignore[misc]


def test_logger_log() -> None:
    """Logger.log should store and return a LogRecord."""
    logger = Logger()

    record = logger.log(
        "INFO",
        "Kernel initialized",
        component="kernel",
    )

    assert record.level == "INFO"
    assert record.message == "Kernel initialized"
    assert record.metadata == {"component": "kernel"}
    assert logger.records == (record,)


def test_logger_info() -> None:
    """Logger.info should create an INFO log."""
    logger = Logger()

    record = logger.info("Ready")

    assert record.level == "INFO"
    assert logger.records[-1] is record


def test_logger_warning() -> None:
    """Logger.warning should create a WARNING log."""
    logger = Logger()

    record = logger.warning("Low memory")

    assert record.level == "WARNING"
    assert logger.records[-1] is record


def test_logger_error() -> None:
    """Logger.error should create an ERROR log."""
    logger = Logger()

    record = logger.error("Crash detected")

    assert record.level == "ERROR"
    assert logger.records[-1] is record


def test_logger_records_property() -> None:
    """records should expose an immutable tuple."""
    logger = Logger()

    logger.info("First")
    logger.warning("Second")

    records = logger.records

    assert isinstance(records, tuple)
    assert len(records) == 2
    assert records[0].message == "First"
    assert records[1].message == "Second"


def test_logger_clear() -> None:
    """clear should remove all stored records."""
    logger = Logger()

    logger.info("One")
    logger.error("Two")

    assert len(logger.records) == 2

    logger.clear()

    assert logger.records == ()