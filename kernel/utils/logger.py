

"""
Reusable logging utility for the Kernel project.
Provides centralized logger configuration and retrieval.
"""

import logging
import sys
from pathlib import Path

# Logging configuration constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class KernelLogger:
    """Reusable logger configuration and retrieval for Kernel."""
    _configured = False

    @classmethod
    def configure(
        cls,
        log_directory: Path | None = None,
        level: int = DEFAULT_LOG_LEVEL,
    ) -> None:
        """
        Configure the root logger with console and optional file output.
        Idempotent: does nothing if already configured.
        """
        if cls._configured:
            return

        handlers = []
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

        # Optional file handler
        if log_directory is not None:
            log_directory.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_directory / "jarvis.log")
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        for handler in handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(level)
        # Silence verbose HTTP client libraries.
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.handlers.clear()
        httpx_logger.setLevel(logging.WARNING)
        httpx_logger.propagate = False

        httpcore_logger = logging.getLogger("httpcore")
        httpcore_logger.handlers.clear()
        httpcore_logger.setLevel(logging.WARNING)
        httpcore_logger.propagate = False

        root_logger.debug("Kernel logging configured")

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger by name.
        """
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger by name.
    """
    return KernelLogger.get_logger(name)