
from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)

"""Memory capability adapter for the JARVIS Kernel."""


class MemoryAdapter(CapabilityAdapter):

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        self._initialized = True

    async def shutdown(self):
        self._initialized = False

    async def health_check(self):
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent in {"remember", "recall", "search_memory", "forget"}

    @property
    def name(self) -> str:
        return "memory"

    @property
    def capability_type(self) -> str:
        return "memory"

    @property
    def description(self) -> str:
        return "Provides long-term and working memory capabilities."

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("MemoryAdapter is not initialized.")
        if not self.supports(task.intent):
            raise ValueError(f"Intent '{task.intent}' not supported by MemoryAdapter.")

        placeholder_messages = {
            "remember": "Remember placeholder.",
            "recall": "Recall placeholder.",
            "search_memory": "Search memory placeholder.",
            "forget": "Forget placeholder.",
        }
        message = placeholder_messages[task.intent]
        result_data = {
            "intent": task.intent,
            "payload": task.payload,
            "message": message,
            "context": task.context,
        }
        return CapabilityResult(
            success=True,
            data=result_data,
            metadata={
                "adapter": self.name,
                "status": "placeholder",
            },
            execution_time_ms=0.0,
        )