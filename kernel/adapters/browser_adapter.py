

"""Browser capability adapter for the JARVIS Kernel."""

from __future__ import annotations

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)


class BrowserAdapter(CapabilityAdapter):
    """
    Capability adapter for browser automation and web interaction.
    """

    def __init__(self) -> None:
        self._initialized = False

    @property
    def name(self) -> str:
        return "browser"

    @property
    def capability_type(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return "Provides browser automation and web interaction capabilities."

    async def initialize(self) -> None:
        self._initialized = True

    async def health_check(self) -> bool:
        return self._initialized

    def supports(self, intent: str) -> bool:
        supported_intents = {
            "browser",
            "browse",
            "web_search",
            "open_url",
            "extract_page",
            "scrape",
            "navigate",
        }
        return intent in supported_intents

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("BrowserAdapter has not been initialized.")

        intent_message_map = {
            "web_search": "Web search placeholder.",
            "open_url": "Open URL placeholder.",
            "extract_page": "Page extraction placeholder.",
            "scrape": "Web scraping placeholder.",
            "navigate": "Browser navigation placeholder.",
            "browser": "Generic browser placeholder.",
            "browse": "Generic browser placeholder.",
        }
        message = intent_message_map.get(task.intent, "Browser adapter placeholder executed successfully.")
        data = {
            "intent": task.intent,
            "payload": task.payload,
            "context": task.context,
            "message": message,
        }
        metadata = {
            "adapter": self.name,
            "status": "placeholder",
        }
        return CapabilityResult(
            success=True,
            data=data,
            metadata=metadata,
            execution_time_ms=0.0,
        )

    async def shutdown(self) -> None:
        self._initialized = False