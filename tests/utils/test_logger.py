"""Unit tests for the centralized logging utility."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from kernel.utils.logger import (
    DEFAULT_DATE_FORMAT,
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    KernelLogger,
    get_logger,
)


@pytest.fixture(autouse=True)
def isolated_logging() -> None:
    """Snapshot and restore global logging state around each test.

    KernelLogger.configure() mutates the root logger, the class-level
    _configured flag, and the httpx/httpcore loggers. This fixture
    guarantees those changes never leak into other tests.
    """
    root_logger = logging.getLogger()
    httpx_logger = logging.getLogger("httpx")
    httpcore_logger = logging.getLogger("httpcore")

    saved = {
        "configured": KernelLogger._configured,
        "root_handlers": list(root_logger.handlers),
        "root_level": root_logger.level,
        "httpx_handlers": list(httpx_logger.handlers),
        "httpx_level": httpx_logger.level,
        "httpx_propagate": httpx_logger.propagate,
        "httpcore_handlers": list(httpcore_logger.handlers),
        "httpcore_level": httpcore_logger.level,
        "httpcore_propagate": httpcore_logger.propagate,
    }

    KernelLogger._configured = False
    yield

    KernelLogger._configured = saved["configured"]
    root_logger.handlers = saved["root_handlers"]
    root_logger.setLevel(saved["root_level"])
    httpx_logger.handlers = saved["httpx_handlers"]
    httpx_logger.setLevel(saved["httpx_level"])
    httpx_logger.propagate = saved["httpx_propagate"]
    httpcore_logger.handlers = saved["httpcore_handlers"]
    httpcore_logger.setLevel(saved["httpcore_level"])
    httpcore_logger.propagate = saved["httpcore_propagate"]


class TestConstants:
    """Tests for module-level logging constants."""

    def test_default_log_level(self) -> None:
        assert DEFAULT_LOG_LEVEL == logging.INFO

    def test_default_log_format(self) -> None:
        assert "%(asctime)s" in DEFAULT_LOG_FORMAT
        assert "%(levelname)-8s" in DEFAULT_LOG_FORMAT
        assert "%(name)-20s" in DEFAULT_LOG_FORMAT
        assert "%(message)s" in DEFAULT_LOG_FORMAT

    def test_default_date_format(self) -> None:
        assert DEFAULT_DATE_FORMAT == "%Y-%m-%d %H:%M:%S"


class TestGetLogger:
    """Tests for logger retrieval."""

    def test_classmethod_returns_logging_logger(self) -> None:
        logger = KernelLogger.get_logger("TestLogger")
        assert isinstance(logger, logging.Logger)

    def test_classmethod_uses_provided_name(self) -> None:
        assert KernelLogger.get_logger("MyComponent").name == "MyComponent"

    def test_classmethod_matches_logging_getlogger(self) -> None:
        assert KernelLogger.get_logger("Shared") is logging.getLogger("Shared")

    def test_module_function_returns_logging_logger(self) -> None:
        logger = get_logger("ModuleLogger")
        assert isinstance(logger, logging.Logger)

    def test_module_function_uses_provided_name(self) -> None:
        assert get_logger("ModuleComponent").name == "ModuleComponent"

    def test_module_function_matches_classmethod(self) -> None:
        assert get_logger("Both") is KernelLogger.get_logger("Both")


class TestConfigureConsole:
    """Tests for console-only configuration."""

    def test_configure_adds_console_handler(self) -> None:
        KernelLogger.configure()
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.formatter is not None

    def test_configure_sets_default_level(self) -> None:
        KernelLogger.configure()
        assert logging.getLogger().level == DEFAULT_LOG_LEVEL

    def test_configure_sets_custom_level(self) -> None:
        KernelLogger.configure(level=logging.DEBUG)
        assert logging.getLogger().level == logging.DEBUG

    def test_configure_clears_existing_handlers(self) -> None:
        root_logger = logging.getLogger()
        stale = logging.StreamHandler()
        root_logger.addHandler(stale)

        KernelLogger.configure()

        assert stale not in root_logger.handlers
        assert len(root_logger.handlers) == 1


class TestConfigureFileOutput:
    """Tests for file handler configuration."""

    def test_configure_creates_log_directory(self, tmp_path: Path) -> None:
        log_directory = tmp_path / "nested" / "logs"
        KernelLogger.configure(log_directory=log_directory)
        assert log_directory.is_dir()

    def test_configure_creates_jarvis_log_file(self, tmp_path: Path) -> None:
        log_directory = tmp_path / "logs"
        KernelLogger.configure(log_directory=log_directory)
        assert (log_directory / "jarvis.log").exists()

    def test_configure_adds_file_handler(self, tmp_path: Path) -> None:
        KernelLogger.configure(log_directory=tmp_path / "logs")
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 2
        assert any(
            isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
        )

    def test_configure_file_handler_points_to_jarvis_log(self, tmp_path: Path) -> None:
        log_directory = tmp_path / "logs"
        KernelLogger.configure(log_directory=log_directory)
        root_logger = logging.getLogger()
        file_handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == str(log_directory / "jarvis.log")


class TestConfigureIdempotency:
    """Tests for the idempotent configure behavior."""

    def test_configure_twice_adds_no_extra_handlers(self) -> None:
        KernelLogger.configure()
        KernelLogger.configure()
        assert len(logging.getLogger().handlers) == 1

    def test_configure_twice_keeps_single_file_handler(self, tmp_path: Path) -> None:
        log_directory = tmp_path / "logs"
        KernelLogger.configure(log_directory=log_directory)
        KernelLogger.configure(log_directory=log_directory)
        assert len(logging.getLogger().handlers) == 2

    def test_configure_noop_when_already_configured(self) -> None:
        KernelLogger._configured = True
        KernelLogger.configure(level=logging.DEBUG)
        assert logging.getLogger().level != logging.DEBUG


class TestHttpClientSilencing:
    """Tests for silencing verbose HTTP client libraries."""

    def test_httpx_logger_silenced(self) -> None:
        KernelLogger.configure()
        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.WARNING
        assert httpx_logger.propagate is False
        assert httpx_logger.handlers == []

    def test_httpcore_logger_silenced(self) -> None:
        KernelLogger.configure()
        httpcore_logger = logging.getLogger("httpcore")
        assert httpcore_logger.level == logging.WARNING
        assert httpcore_logger.propagate is False
        assert httpcore_logger.handlers == []

    def test_httpx_handlers_cleared(self) -> None:
        httpx_logger = logging.getLogger("httpx")
        stale = logging.StreamHandler()
        httpx_logger.addHandler(stale)

        KernelLogger.configure()

        assert stale not in httpx_logger.handlers
        assert httpx_logger.handlers == []

    def test_httpcore_handlers_cleared(self) -> None:
        httpcore_logger = logging.getLogger("httpcore")
        stale = logging.StreamHandler()
        httpcore_logger.addHandler(stale)

        KernelLogger.configure()

        assert stale not in httpcore_logger.handlers
        assert httpcore_logger.handlers == []


class TestConfigureConfirmation:
    """Tests for the configuration confirmation log message."""

    def test_configure_logs_confirmation(self) -> None:
        messages: list[str] = []
        original_debug = logging.getLogger().debug

        def spy_debug(message: object, *args: object, **kwargs: object) -> None:
            messages.append(str(message))
            original_debug(message, *args, **kwargs)

        logging.getLogger().debug = spy_debug  # type: ignore[method-assign]
        try:
            KernelLogger.configure()
        finally:
            logging.getLogger().debug = original_debug  # type: ignore[method-assign]

        assert "Kernel logging configured" in messages
