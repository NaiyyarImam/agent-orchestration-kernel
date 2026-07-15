"""Public JARVIS Kernel entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kernel.core.bootstrap import Bootstrap
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.utils.logger import get_logger


class Kernel:
    """Primary entry point for the JARVIS Kernel."""

    def __init__(self, root: str | Path = ".") -> None:
        self._bootstrap = Bootstrap(root)
        self._engine: ExecutiveEngine | None = None
        self._started = False
        self._logger = get_logger("Kernel")

    async def start(self) -> None:
        """Initialize the Kernel."""

        if self._started:
            return

        self._logger.info("Starting JARVIS Kernel")
        self._engine = self._bootstrap.build()
        # Initialize all registered capability adapters.
        for adapter in self._engine.adapters._adapters.values():
            await adapter.initialize()
        self._started = True
        self._logger.info("JARVIS Kernel started successfully")

    async def shutdown(self) -> None:
        """Shutdown the Kernel."""

        if not self._started:
            return

        self._logger.info("Shutting down JARVIS Kernel")

        if self._engine is not None:
            memory_store = self._engine.memory.store

            close = getattr(memory_store, "close", None)
            if callable(close):
                await close()

        self._engine = None
        self._started = False
        self._logger.info("JARVIS Kernel shutdown complete")

    async def health_check(self) -> dict[str, Any]:
        """Return the health of the Kernel."""

        if self._engine is None:
            raise RuntimeError("Kernel has not been started.")

        self._logger.debug("Running Kernel health check")
        return await self._engine.health_check()

    @property
    def engine(self) -> ExecutiveEngine:
        """Return the Executive Engine."""

        if self._engine is None:
            raise RuntimeError("Kernel has not been started.")

        return self._engine

    @property
    def started(self) -> bool:
        """Return True if the Kernel is running."""

        return self._started