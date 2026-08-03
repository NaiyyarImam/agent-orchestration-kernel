"""Research capability adapter for the JARVIS Kernel.

The adapter is a pure translation boundary: it converts a CapabilityTask
into a ResearchBackend search operation and converts the outcome back
into a CapabilityResult.

Boundary responsibilities:
- The adapter owns NO research logic and no search behavior.
- The injected ResearchBackend owns ALL search behavior.
- Bootstrap is the only composition root: it constructs backends and
  injects them; the adapter never instantiates a backend.
- The Kernel never knows which backend is used or how the search is
  performed, or whether the backend is local or remote.
- Every external integration (MCP servers, Tavily, Exa, Perplexity,
  local indexes, hybrid search) stays behind the ResearchBackend
  interface.

The backend contract (ResearchBackend, ResearchResult) is defined in
kernel.interfaces.research_backend; this adapter only imports it.
"""

from __future__ import annotations

import time
from typing import Any

from kernel.interfaces.capability_adapter import (
    CapabilityAdapter,
    CapabilityResult,
    CapabilityTask,
)
from kernel.interfaces.research_backend import ResearchBackend, ResearchResult

_RESEARCH_INTENTS: frozenset[str] = frozenset(
    {"research", "search", "analyze", "investigate", "summarize"}
)

_DEFAULT_SEARCH_LIMIT: int = 10


class ResearchAdapter(CapabilityAdapter):
    """Framework-independent research adapter.

    Delegates every search to the injected ResearchBackend and
    translates the outcome into a CapabilityResult. Optional backend
    lifecycle hooks (initialize/shutdown/health_check) and metadata
    (name/description/capabilities) are discovered dynamically, so
    minimal backends work exactly as before.
    """

    def __init__(self, backend: ResearchBackend | None = None) -> None:
        self._backend = backend
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
        await self._call_backend_hook("initialize")
        self._initialized = True

    async def health_check(self) -> bool:
        if not self._initialized:
            return False
        hook = self._backend_hook("health_check")
        if hook is None:
            return True
        try:
            return bool(await hook())
        except Exception:
            return False

    def supports(self, intent: str) -> bool:
        return intent.lower() in _RESEARCH_INTENTS

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        if not self._initialized:
            raise RuntimeError("ResearchAdapter has not been initialized.")

        intent = task.intent.lower()
        if intent not in _RESEARCH_INTENTS:
            return self._failed(
                task,
                f"Intent '{task.intent}' is not supported by the research adapter.",
            )

        return await self._execute_research(task)

    async def _execute_research(self, task: CapabilityTask) -> CapabilityResult:
        query = self._extract_query(task)
        if query is None:
            return self._failed(task, "Missing 'query' in payload")

        backend = self._backend
        if backend is None:
            return self._failed(
                task,
                "Research backend is not configured for the research adapter.",
            )

        limit, limit_error = self._validate_limit(task)
        if limit_error is not None:
            return self._failed(task, limit_error)

        started = time.perf_counter()
        try:
            findings = await backend.search(
                query,
                limit=limit,
                context=task.context,
            )
        except Exception as exc:
            return self._failed(
                task,
                f"Research operation failed: {exc}",
                execution_time_ms=self._elapsed_ms(started),
            )

        results = self._normalize_findings(findings)
        if results is None:
            return self._failed(
                task,
                "Research backend returned an invalid response: expected "
                "an iterable of ResearchResult or dict items.",
                execution_time_ms=self._elapsed_ms(started),
            )

        return self._ok(
            task,
            data={
                "query": query,
                "results": results,
            },
            execution_time_ms=self._elapsed_ms(started),
        )

    @staticmethod
    def _extract_query(task: CapabilityTask) -> str | None:
        raw = task.payload.get(
            "query", task.payload.get("text", task.payload.get("user_input"))
        )
        if raw is None:
            return None
        value = str(raw).strip()
        return value if value else None

    @staticmethod
    def _validate_limit(task: CapabilityTask) -> tuple[int, str | None]:
        raw_limit = task.payload.get("limit")
        if raw_limit is None:
            return _DEFAULT_SEARCH_LIMIT, None
        if isinstance(raw_limit, (bool, float)):
            return 0, ResearchAdapter._limit_error(raw_limit)
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return 0, ResearchAdapter._limit_error(raw_limit)
        if limit < 1:
            return 0, ResearchAdapter._limit_error(raw_limit)
        return limit, None

    @staticmethod
    def _limit_error(raw_limit: Any) -> str:
        return (
            f"Invalid 'limit' value in payload: {raw_limit!r} "
            "is not a positive integer."
        )

    @staticmethod
    def _normalize_findings(findings: Any) -> list[dict[str, Any]] | None:
        if findings is None:
            return []
        if isinstance(findings, dict):
            return None
        if isinstance(findings, (list, tuple)):
            items: list[Any] = list(findings)
        else:
            try:
                items = list(findings)
            except TypeError:
                return None

        results: list[dict[str, Any]] = []
        for item in items:
            serialized = ResearchAdapter._serialize_result(item)
            if serialized is None:
                return None
            results.append(serialized)
        return results

    @staticmethod
    def _serialize_result(result: Any) -> dict[str, Any] | None:
        if isinstance(result, ResearchResult):
            return {
                "title": result.title,
                "snippet": result.snippet,
                "url": result.url,
                "source": result.source,
            }
        if isinstance(result, dict):
            return dict(result)
        return None

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return (time.perf_counter() - started) * 1000.0

    def _backend_hook(self, method: str) -> Any:
        backend = self._backend
        if backend is None:
            return None
        hook = getattr(backend, method, None)
        return hook if callable(hook) else None

    async def _call_backend_hook(self, method: str) -> None:
        hook = self._backend_hook(method)
        if hook is not None:
            await hook()

    def _ok(
        self,
        task: CapabilityTask,
        *,
        data: dict[str, Any],
        execution_time_ms: float = 0.0,
    ) -> CapabilityResult:
        return CapabilityResult(
            success=True,
            data={
                "intent": task.intent,
                "payload": task.payload,
                "context": task.context,
                **data,
            },
            metadata={
                "adapter": self.name,
                "status": "ok",
            },
            execution_time_ms=execution_time_ms,
        )

    def _failed(
        self,
        task: CapabilityTask,
        error: str,
        *,
        execution_time_ms: float = 0.0,
    ) -> CapabilityResult:
        return CapabilityResult(
            success=False,
            error=error,
            metadata={
                "adapter": self.name,
                "status": "error",
            },
            execution_time_ms=execution_time_ms,
        )

    async def shutdown(self) -> None:
        self._initialized = False
        await self._call_backend_hook("shutdown")
