"""Entry point for the JARVIS Kernel."""

from __future__ import annotations

import asyncio
import sys
from typing import Any


from kernel.core.kernel import Kernel
from kernel.utils.logger import get_logger


BANNER = r"""
=========================================================
                     JARVIS KERNEL
                        Version 0.1
=========================================================
"""


def _status_label(status: Any) -> str:
    """Return 'OK' or 'FAILED' for a health value.

    Nested health dictionaries (for example model provider health)
    are evaluated by their contained values, never by truthiness of
    the dictionary itself.
    """
    if isinstance(status, dict):
        if not status:
            return "FAILED"
        return "OK" if all(status.values()) else "FAILED"
    return "OK" if status else "FAILED"


def render_health(health: dict[str, Any]) -> list[str]:
    """Render component health lines, expanding nested health dicts."""
    lines: list[str] = []
    for component, status in health.items():
        lines.append(f"{component:<15}{_status_label(status)}")
        if isinstance(status, dict):
            for sub_component, sub_status in status.items():
                lines.append(f"  {sub_component:<13}{_status_label(sub_status)}")
    return lines


async def main() -> None:
    """Start the JARVIS Kernel."""
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
        for line in render_health(health):
            print(line)

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

        
