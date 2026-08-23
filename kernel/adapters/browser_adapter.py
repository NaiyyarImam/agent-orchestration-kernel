"""Browser capability adapter for the JARVIS Kernel."""

from __future__ import annotations

import time

from kernel.interfaces.browser_backend import BrowserBackend
from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)


class BrowserAdapter(CapabilityAdapter):
    """Browser capability adapter.

    Delegates browser operations to an injected BrowserBackend.
    """

    def __init__(self, backend: BrowserBackend | None = None) -> None:
        self._backend = backend
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
        if self._backend is not None:
            await self._backend.initialize()
        self._initialized = True

    async def health_check(self) -> bool:
        if not self._initialized:
            return False
        if self._backend is not None:
            return await self._backend.health_check()
        return True

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

        backend = self._backend
        if backend is None:
            return CapabilityResult(
                success=False,
                error="Browser backend is not configured",
                metadata={"adapter": self.name, "status": "error"},
                execution_time_ms=0.0,
            )

        intent = task.intent
        payload = task.payload
        started = time.perf_counter()

        try:
            if intent in ("open_url", "navigate", "browse"):
                url = payload.get("url")
                if not url:
                    return self._failed(task, "Missing 'url' in payload", started)
                result = await backend.navigate(url, timeout=payload.get("timeout"))
            elif intent == "web_search":
                query = payload.get("query") or payload.get("text")
                if not query:
                    return self._failed(task, "Missing 'query' in payload", started)
                result = await backend.search(query, limit=payload.get("limit", 10), timeout=payload.get("timeout"))
            elif intent in ("extract_page", "scrape"):
                selector = payload.get("selector")
                result = await backend.extract(selector)
            else:
                return self._failed(task, f"Intent '{intent}' not implemented", started)

            execution_ms = (time.perf_counter() - started) * 1000.0

            if result.success:
                return CapabilityResult(
                    success=True,
                    data={
                        "intent": intent,
                        "payload": payload,
                        "url": result.url,
                        "title": result.title,
                        "content": result.content,
                        "data": result.data,
                    },
                    metadata={"adapter": self.name, "status": "ok"},
                    execution_time_ms=execution_ms,
                )
            else:
                return CapabilityResult(
                    success=False,
                    error=result.error,
                    metadata={"adapter": self.name, "status": "error"},
                    execution_time_ms=execution_ms,
                )

        except Exception as exc:
            return self._failed(task, f"Browser operation failed: {exc}", started)

    def _failed(self, task: CapabilityTask, error: str, started: float) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            error=error,
            metadata={"adapter": self.name, "status": "error"},
            execution_time_ms=(time.perf_counter() - started) * 1000.0,
        )

    async def shutdown(self) -> None:
        if self._backend is not None:
            await self._backend.shutdown()
        self._initialized = False