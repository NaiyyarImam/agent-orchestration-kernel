

"""Research capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)


class ResearchAdapter(CapabilityAdapter):
    """Framework-independent research adapter."""

    def __init__(self) -> None:
        self._initialized = False

    @property
    def name(self) -> str:
        return "research"

    @property
    def capability_type(self) -> str:
        return "research"

    @property
    def description(self) -> str:
        return "Provides research and knowledge retrieval capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent.lower() in {
            "research",
            "search",
            "analyze",
            "investigate",
            "summarize",
        }

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("ResearchAdapter has not been initialized.")

        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "payload": task.payload,
                "context": task.context,
                "message": "Research adapter placeholder executed successfully.",
            },
            metadata={
                "adapter": self.name,
                "status": "placeholder",
            },
            execution_time_ms=0.0,
        )

    async def shutdown(self) -> None:
        self._initialized = False