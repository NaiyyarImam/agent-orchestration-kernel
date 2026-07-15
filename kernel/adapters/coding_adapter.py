

"""Coding capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)


class CodingAdapter(CapabilityAdapter):
    """Framework-independent coding capability adapter."""

    def __init__(self) -> None:
        self._initialized = False

    @property
    def name(self) -> str:
        return "coding"

    @property
    def capability_type(self) -> str:
        return "coding"

    @property
    def description(self) -> str:
        return "Provides code generation, explanation, and review capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        return intent.lower() in {
            "code",
            "coding",
            "generate_code",
            "explain_code",
            "review_code",
            "refactor_code",
            "debug_code",
            "test_code",
        }

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("CodingAdapter has not been initialized.")

        handlers = {
            "generate_code": "Generated code placeholder.",
            "explain_code": "Code explanation placeholder.",
            "review_code": "Code review placeholder.",
            "refactor_code": "Code refactoring placeholder.",
            "debug_code": "Code debugging placeholder.",
            "test_code": "Test generation placeholder.",
            "code": "Generic coding placeholder.",
            "coding": "Generic coding placeholder.",
        }

        message = handlers.get(
            task.intent,
            "Coding adapter placeholder executed successfully.",
        )

        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "payload": task.payload,
                "context": task.context,
                "message": message,
            },
            metadata={
                "adapter": self.name,
                "status": "placeholder",
            },
            execution_time_ms=0.0,
        )

    async def shutdown(self) -> None:
        self._initialized = False