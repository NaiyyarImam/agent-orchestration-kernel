"""Entry point for the JARVIS Kernel."""

from __future__ import annotations

import asyncio
import sys


from kernel.core.kernel import Kernel
from kernel.config.config_manager import ConfigManager
from kernel.utils.logger import KernelLogger, get_logger


BANNER = r"""
=========================================================
                     JARVIS KERNEL
                        Version 0.1
=========================================================
"""


async def main() -> None:
    """Start the JARVIS Kernel."""
    config = ConfigManager()

    KernelLogger.configure(
        log_directory=config.storage.root / "logs"
    )

    logger = get_logger("Main")

    print(BANNER)

    kernel = Kernel()

    try:
        print("[1/4] Starting Kernel...")
        logger.info("Launching JARVIS Kernel")
        await kernel.start()
        print("✓ Kernel started")

        print("[2/4] Running health check...")
        health = await kernel.health_check()
        logger.info("Kernel health check completed")

        print("\n========== COMPONENT HEALTH ==========")
        for component, status in health.items():
            print(
                f"{component:<15}"
                f"{'OK' if status else 'FAILED'}"
            )

        print("======================================")
        print("\n✓ JARVIS Kernel is ready.")

    except Exception as exc:
        logger.exception("Kernel startup failed")
        print(f"\nKernel startup failed:\n{exc}")
        raise

    finally:
        logger.info("Shutting down JARVIS Kernel")
        print("\n[4/4] Shutting down...")
        await kernel.shutdown()
        print("✓ Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)

        