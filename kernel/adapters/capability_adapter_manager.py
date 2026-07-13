"""Capability Adapter Manager for the JARVIS Kernel.

This manager owns the lifecycle of all capability adapters.

The Executive Engine must communicate with adapters only through this
manager. Adapters themselves implement the CapabilityAdapter interface.
"""

from __future__ import annotations

from typing import Any

from kernel.interfaces.capability_adapter import CapabilityAdapter


class CapabilityAdapterManager:
    """Central registry and dispatcher for capability adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, CapabilityAdapter] = {}

    def register(self, adapter: CapabilityAdapter) -> None:
        """Register a capability adapter."""

        if adapter.name in self._adapters:
            raise ValueError(
                f"Adapter '{adapter.name}' is already registered."
            )

        self._adapters[adapter.name] = adapter

    def unregister(self, adapter_name: str) -> bool:
        """Remove an adapter."""

        return self._adapters.pop(adapter_name, None) is not None

    def get(self, adapter_name: str) -> CapabilityAdapter:
        """Return a registered adapter."""

        try:
            return self._adapters[adapter_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown adapter: {adapter_name}"
            ) from exc

    def exists(self, adapter_name: str) -> bool:
        """Return True if an adapter is registered."""

        return adapter_name in self._adapters

    def list_adapters(self) -> list[str]:
        """Return registered adapter names."""

        return sorted(self._adapters.keys())

    @property
    def count(self) -> int:
        """Return number of registered adapters."""

        return len(self._adapters)

    async def execute(
        self,
        adapter_name: str,
        task: str,
        **kwargs: Any,
    ) -> Any:
        """Execute a task using the specified adapter."""

        adapter = self.get(adapter_name)

        return await adapter.execute(
            task=task,
            **kwargs,
        )

    async def health_check(self) -> bool:
        """Return overall adapter manager health."""

        # An empty registry is considered healthy during bootstrap.
        if not self._adapters:
            return True

        results = []
        for adapter in self._adapters.values():
            results.append(await adapter.health_check())

        return all(results)

    async def initialize_all(self) -> None:
        """Initialize every registered adapter."""

        for adapter in self._adapters.values():
            await adapter.initialize()

    async def shutdown_all(self) -> None:
        """Shutdown every registered adapter."""

        for adapter in self._adapters.values():
            await adapter.shutdown()

    def clear(self) -> None:
        """Remove every registered adapter."""

        self._adapters.clear()