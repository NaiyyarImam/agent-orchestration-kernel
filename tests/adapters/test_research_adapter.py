"""Tests for the ResearchAdapter production implementation."""

from __future__ import annotations

from typing import Any

import pytest

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.core.bootstrap import Bootstrap
from kernel.interfaces import ResearchBackend, ResearchResult
from kernel.interfaces.capability_adapter import CapabilityTask
from kernel.policy import PolicyEngine, PolicyRule

RESEARCH_POLICY_RULES = [
    PolicyRule(intent="research", allowed=True),
    PolicyRule(intent="search", allowed=True),
    PolicyRule(intent="analyze", allowed=True),
    PolicyRule(intent="investigate", allowed=True),
    PolicyRule(intent="summarize", allowed=True),
]

DEFAULT_FINDINGS = [
    ResearchResult(
        title="JARVIS Kernel",
        snippet="An open-source kernel architecture.",
        url="https://example.com/jarvis",
        source="fake",
    ),
    ResearchResult(
        title="JARVIS Usage",
        snippet="How to use the JARVIS Kernel.",
        url="https://example.com/jarvis-usage",
        source="fake",
    ),
]


class FakeResearchBackend:
    """Deterministic in-memory ResearchBackend for tests."""

    def __init__(self, findings: list[ResearchResult] | None = None) -> None:
        self._findings = findings if findings is not None else list(DEFAULT_FINDINGS)
        self.fail = False
        self.calls: list[dict[str, Any]] = []

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        context: dict[str, Any] | None = None,
    ) -> list[ResearchResult]:
        self.calls.append({"query": query, "limit": limit, "context": context})
        if self.fail:
            raise RuntimeError("backend exploded")
        return list(self._findings[:limit])


class TestAdapterContract:
    """Tests for the ResearchAdapter contract (metadata, lifecycle, intents)."""

    @pytest.fixture
    def adapter(self) -> ResearchAdapter:
        return ResearchAdapter()

    def test_adapter_metadata(self, adapter: ResearchAdapter) -> None:
        assert adapter.name == "research"
        assert adapter.capability_type == "research"
        assert isinstance(adapter.description, str)
        assert adapter.description.strip() != ""

    @pytest.mark.asyncio
    async def test_initialize_and_health_check(self, adapter: ResearchAdapter) -> None:
        assert await adapter.health_check() is False
        await adapter.initialize()
        assert await adapter.health_check() is True

    @pytest.mark.asyncio
    async def test_shutdown(self, adapter: ResearchAdapter) -> None:
        await adapter.initialize()
        assert await adapter.health_check() is True
        await adapter.shutdown()
        assert await adapter.health_check() is False

    @pytest.mark.parametrize(
        "intent",
        ["research", "search", "analyze", "investigate", "summarize"],
    )
    def test_supported_intents(self, adapter: ResearchAdapter, intent: str) -> None:
        assert adapter.supports(intent) is True

    def test_supported_intents_are_case_insensitive(
        self, adapter: ResearchAdapter
    ) -> None:
        assert adapter.supports("Research") is True

    def test_unsupported_intent(self, adapter: ResearchAdapter) -> None:
        assert adapter.supports("coding") is False
        assert adapter.supports("remember") is False

    @pytest.mark.asyncio
    async def test_execute_requires_initialize(self, adapter: ResearchAdapter) -> None:
        with pytest.raises(RuntimeError):
            await adapter.execute(
                CapabilityTask(task_id="t", intent="research", payload={})
            )

    @pytest.mark.asyncio
    async def test_unsupported_intent_returns_failed_result(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="coding", payload={"query": "x"})
        )
        assert result.success is False
        assert "not supported" in result.error
        assert result.metadata["adapter"] == "research"
        assert result.metadata["status"] == "error"


class TestResearchInterfaceRelocation:
    """The backend contract lives in kernel.interfaces, not the adapter."""

    def test_contract_is_exported_from_interfaces_package(self) -> None:
        from kernel.interfaces import ResearchBackend as PkgBackend
        from kernel.interfaces import ResearchResult as PkgResult

        assert PkgBackend is ResearchBackend
        assert PkgResult is ResearchResult

    def test_adapter_only_imports_the_interface(self) -> None:
        from kernel.adapters.research_adapter import (
            ResearchBackend as AdapterBackend,
        )
        from kernel.adapters.research_adapter import (
            ResearchResult as AdapterResult,
        )

        assert AdapterBackend.__module__ == "kernel.interfaces.research_backend"
        assert AdapterResult.__module__ == "kernel.interfaces.research_backend"

    def test_interface_checks_only_the_search_member(self) -> None:
        assert ResearchBackend.__protocol_attrs__ == {"search"}

    def test_metadata_and_lifecycle_hooks_are_documented_but_optional(
        self,
    ) -> None:
        doc = ResearchBackend.__doc__ or ""
        for member in (
            "initialize",
            "shutdown",
            "health_check",
            "name",
            "description",
            "capabilities",
        ):
            assert member in doc, f"{member} must be documented on the port"
        assert isinstance(FakeResearchBackend(), ResearchBackend)


class TestResearchOperations:
    """Tests for the real research operation delegated to the backend."""

    @pytest.fixture
    def backend(self) -> FakeResearchBackend:
        return FakeResearchBackend()

    @pytest.fixture
    def adapter(self, backend: FakeResearchBackend) -> ResearchAdapter:
        return ResearchAdapter(backend)

    @pytest.mark.asyncio
    async def test_research_returns_findings(
        self, adapter: ResearchAdapter, backend: FakeResearchBackend
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "JARVIS"},
            )
        )
        assert result.success is True
        assert result.data["intent"] == "research"
        assert result.data["payload"] == {"query": "JARVIS"}
        assert result.data["query"] == "JARVIS"
        assert result.data["results"] == [
            {
                "title": "JARVIS Kernel",
                "snippet": "An open-source kernel architecture.",
                "url": "https://example.com/jarvis",
                "source": "fake",
            },
            {
                "title": "JARVIS Usage",
                "snippet": "How to use the JARVIS Kernel.",
                "url": "https://example.com/jarvis-usage",
                "source": "fake",
            },
        ]
        assert result.metadata["adapter"] == "research"
        assert result.metadata["status"] == "ok"
        assert result.execution_time_ms >= 0.0
        assert backend.calls[0]["query"] == "JARVIS"
        assert backend.calls[0]["limit"] == 10
        assert backend.calls[0]["context"] == {}

    @pytest.mark.asyncio
    async def test_research_with_text_payload(
        self, adapter: ResearchAdapter, backend: FakeResearchBackend
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="search", payload={"text": "kernel"})
        )
        assert result.success is True
        assert result.data["query"] == "kernel"
        assert backend.calls[0]["query"] == "kernel"

    @pytest.mark.asyncio
    async def test_research_with_user_input_payload(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"user_input": "Research JARVIS"},
            )
        )
        assert result.success is True
        assert result.data["query"] == "Research JARVIS"

    @pytest.mark.asyncio
    async def test_synonym_intents_route_to_research(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        for intent in ["search", "analyze", "investigate", "summarize"]:
            result = await adapter.execute(
                CapabilityTask(task_id="t", intent=intent, payload={"query": "q"})
            )
            assert result.success is True, intent
            assert result.data["intent"] == intent

    @pytest.mark.asyncio
    async def test_missing_query(self, adapter: ResearchAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={})
        )
        assert result.success is False
        assert "Missing 'query'" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_blank_query(self, adapter: ResearchAdapter) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "   "})
        )
        assert result.success is False
        assert "Missing 'query'" in result.error

    @pytest.mark.asyncio
    async def test_limit_is_honored(
        self, adapter: ResearchAdapter, backend: FakeResearchBackend
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t", intent="research", payload={"query": "q", "limit": 1}
            )
        )
        assert result.success is True
        assert len(result.data["results"]) == 1
        assert backend.calls[0]["limit"] == 1

    @pytest.mark.asyncio
    async def test_invalid_limit_is_failed_result(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "q", "limit": "many"},
            )
        )
        assert result.success is False
        assert "Invalid 'limit'" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_zero_limit_is_failed_result(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "q", "limit": 0},
            )
        )
        assert result.success is False
        assert "Invalid 'limit'" in result.error

    @pytest.mark.asyncio
    async def test_negative_limit_is_failed_result(
        self, adapter: ResearchAdapter
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "q", "limit": -3},
            )
        )
        assert result.success is False
        assert "Invalid 'limit'" in result.error

    @pytest.mark.parametrize(
        "raw_limit",
        ["0", "-1", "many", 2.5, 1.9, True, False, [], {}],
    )
    @pytest.mark.asyncio
    async def test_invalid_limit_values_never_reach_backend(
        self,
        adapter: ResearchAdapter,
        backend: FakeResearchBackend,
        raw_limit: Any,
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "q", "limit": raw_limit},
            )
        )
        assert result.success is False
        assert "Invalid 'limit'" in result.error
        assert not backend.calls, "The backend must not run with an invalid limit"

    @pytest.mark.asyncio
    async def test_numeric_string_limit_is_honored(
        self, adapter: ResearchAdapter, backend: FakeResearchBackend
    ) -> None:
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(
                task_id="t",
                intent="research",
                payload={"query": "q", "limit": "1"},
            )
        )
        assert result.success is True
        assert len(result.data["results"]) == 1
        assert backend.calls[0]["limit"] == 1

    @pytest.mark.asyncio
    async def test_backend_may_return_plain_dicts(self) -> None:
        class DictBackend:
            async def search(
                self, query: str, **kwargs: Any
            ) -> list[dict[str, Any]]:
                return [{"title": "t", "snippet": "s"}]

        adapter = ResearchAdapter(DictBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert result.data["results"] == [{"title": "t", "snippet": "s"}]

    @pytest.mark.asyncio
    async def test_empty_findings_are_successful(
        self, adapter: ResearchAdapter
    ) -> None:
        empty = FakeResearchBackend(findings=[])
        bare = ResearchAdapter(empty)
        await bare.initialize()
        result = await bare.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert result.data["results"] == []

    @pytest.mark.asyncio
    async def test_none_backend_response_is_empty_success(self) -> None:
        class NoneBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return None

        adapter = ResearchAdapter(NoneBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert result.data["results"] == []

    @pytest.mark.asyncio
    async def test_tuple_backend_response_is_success(self) -> None:
        class TupleBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return tuple(DEFAULT_FINDINGS)

        adapter = ResearchAdapter(TupleBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert len(result.data["results"]) == 2

    @pytest.mark.asyncio
    async def test_generator_backend_response_is_success(self) -> None:
        class GeneratorBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return (item for item in DEFAULT_FINDINGS)

        adapter = ResearchAdapter(GeneratorBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert len(result.data["results"]) == 2

    @pytest.mark.asyncio
    async def test_malformed_backend_response_is_failed_result(self) -> None:
        class MalformedBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return 42

        adapter = ResearchAdapter(MalformedBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "invalid response" in result.error
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_dict_backend_response_is_failed_result(self) -> None:
        class DictResponseBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return {"title": "t", "snippet": "s"}

        adapter = ResearchAdapter(DictResponseBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "invalid response" in result.error

    @pytest.mark.asyncio
    async def test_invalid_result_object_type_is_failed_result(self) -> None:
        class JunkBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return [object()]

        adapter = ResearchAdapter(JunkBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "invalid response" in result.error

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_results_fail_entire_response(
        self,
    ) -> None:
        class MixedBackend:
            async def search(self, query: str, **kwargs: Any) -> Any:
                return [DEFAULT_FINDINGS[0], "not-a-result"]

        adapter = ResearchAdapter(MixedBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "invalid response" in result.error

    @pytest.mark.asyncio
    async def test_backend_failure_becomes_failed_result(
        self, adapter: ResearchAdapter, backend: FakeResearchBackend
    ) -> None:
        backend.fail = True
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "Research operation failed" in result.error
        assert "backend exploded" in result.error
        assert result.metadata["adapter"] == "research"
        assert result.metadata["status"] == "error"

    @pytest.mark.asyncio
    async def test_backend_exception_never_leaks(self) -> None:
        class ExplodingBackend:
            async def search(self, query: str, **kwargs: Any) -> list[ResearchResult]:
                raise ConnectionError("remote backend unavailable")

        adapter = ResearchAdapter(ExplodingBackend())
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "remote backend unavailable" in result.error

    @pytest.mark.asyncio
    async def test_backend_not_configured(self) -> None:
        adapter = ResearchAdapter()
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "Research backend is not configured" in result.error
        assert result.metadata["status"] == "error"


class TestResearchDependencyInjection:
    """Tests for constructor-injected backend dependency."""

    @pytest.mark.asyncio
    async def test_backend_is_injected_through_constructor(self) -> None:
        backend = FakeResearchBackend()
        adapter = ResearchAdapter(backend=backend)
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert backend.calls, "The injected backend must be the one executed"

    @pytest.mark.asyncio
    async def test_adapter_without_backend_never_calls_search(self) -> None:
        adapter = ResearchAdapter()
        await adapter.initialize()
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is False
        assert "not configured" in result.error

    def test_backend_port_is_protocol_typed(self) -> None:
        backend = FakeResearchBackend()
        assert isinstance(backend, ResearchBackend)


class LifecycleBackend:
    """ResearchBackend that advertises optional lifecycle hooks."""

    def __init__(self) -> None:
        self.initialize_called = False
        self.shutdown_called = False
        self.healthy = True

    async def initialize(self) -> None:
        self.initialize_called = True

    async def shutdown(self) -> None:
        self.shutdown_called = True

    async def health_check(self) -> bool:
        return self.healthy

    async def search(self, query: str, **kwargs: Any) -> list[ResearchResult]:
        return []


class TestResearchBackendLifecycleHooks:
    """Optional backend lifecycle hooks are discovered and honored."""

    @pytest.mark.asyncio
    async def test_adapter_invokes_backend_initialize(self) -> None:
        backend = LifecycleBackend()
        adapter = ResearchAdapter(backend)
        await adapter.initialize()
        assert backend.initialize_called is True
        assert await adapter.health_check() is True

    @pytest.mark.asyncio
    async def test_adapter_invokes_backend_shutdown(self) -> None:
        backend = LifecycleBackend()
        adapter = ResearchAdapter(backend)
        await adapter.initialize()
        await adapter.shutdown()
        assert backend.shutdown_called is True
        assert await adapter.health_check() is False

    @pytest.mark.asyncio
    async def test_adapter_health_check_delegates_to_backend(self) -> None:
        backend = LifecycleBackend()
        adapter = ResearchAdapter(backend)
        await adapter.initialize()
        assert await adapter.health_check() is True
        backend.healthy = False
        assert await adapter.health_check() is False

    @pytest.mark.asyncio
    async def test_backend_health_check_failure_reports_unhealthy(self) -> None:
        class BrokenHealthBackend:
            async def health_check(self) -> bool:
                raise RuntimeError("health probe failed")

            async def search(self, query: str, **kwargs: Any) -> Any:
                return []

        adapter = ResearchAdapter(BrokenHealthBackend())
        await adapter.initialize()
        assert await adapter.health_check() is False

    @pytest.mark.asyncio
    async def test_backend_without_hooks_works_exactly_as_before(self) -> None:
        backend = FakeResearchBackend()
        adapter = ResearchAdapter(backend)
        await adapter.initialize()
        assert await adapter.health_check() is True
        result = await adapter.execute(
            CapabilityTask(task_id="t", intent="research", payload={"query": "q"})
        )
        assert result.success is True
        assert backend.calls
        await adapter.shutdown()
        assert await adapter.health_check() is False

    @pytest.mark.asyncio
    async def test_backend_without_hooks_is_still_protocol_compliant(
        self,
    ) -> None:
        assert isinstance(FakeResearchBackend(), ResearchBackend)
        assert isinstance(LifecycleBackend(), ResearchBackend)


class TestResearchThroughManager:
    """End-to-end dispatch through the CapabilityAdapterManager."""

    @pytest.fixture
    def manager(self) -> tuple[CapabilityAdapterManager, FakeResearchBackend]:
        backend = FakeResearchBackend()
        manager = CapabilityAdapterManager()
        manager.register(ResearchAdapter(backend))
        return manager, backend

    @pytest.mark.asyncio
    async def test_research_dispatches_through_manager(
        self, manager: tuple[CapabilityAdapterManager, FakeResearchBackend]
    ) -> None:
        manager, backend = manager
        await manager.initialize_all()
        result = await manager.execute(
            CapabilityTask(
                task_id="t1",
                intent="research",
                payload={"query": "JARVIS"},
            )
        )
        assert result.success is True
        assert result.metadata["adapter"] == "research"
        assert result.data["results"]
        assert backend.calls

    @pytest.mark.asyncio
    async def test_manager_resolves_research_intent(
        self, manager: tuple[CapabilityAdapterManager, FakeResearchBackend]
    ) -> None:
        manager, _ = manager
        assert manager.can_handle("research") is True
        assert manager.find_adapter_for_intent("research").name == "research"


class TestResearchThroughExecutiveEngine:
    """End-to-end execution through the composed Kernel ExecutiveEngine."""

    @pytest.mark.asyncio
    async def test_research_executes_through_composed_kernel(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            result = await engine.execute_capability(
                "research",
                {"query": "JARVIS"},
            )
            assert result.success is False
            assert "Research backend is not configured" in result.error
            assert result.metadata["adapter"] == "research"
            assert result.metadata["status"] == "error"
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_pipeline_with_injected_backend(
        self, tmp_path, monkeypatch
    ) -> None:
        """Full pipeline with a backend behind the adapter boundary."""
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        backend = FakeResearchBackend()
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            engine.adapters.unregister("research")
            research = ResearchAdapter(backend)
            await research.initialize()
            engine.adapters.register(research)

            results = await engine.execute_request("Research JARVIS")
            assert results[0].success is True
            assert results[0].data["status"] == "COMPLETED"
            assert results[0].metadata["capability"] == "research"
            assert results[0].metadata["adapter"] == "research"

            capability_result = results[0].metadata["capability_result"]
            assert capability_result["query"] == "Research JARVIS"
            assert capability_result["results"]
            assert backend.calls
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_pipeline_reports_unconfigured_backend(
        self, tmp_path, monkeypatch
    ) -> None:
        """The pipeline completes honestly when no backend is configured."""
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            results = await engine.execute_request("Research JARVIS")
            assert results[0].success is False
            assert results[0].data["status"] == "FAILED"
            assert results[0].metadata["capability"] == "research"
            assert results[0].metadata["adapter"] == "research"
            assert results[0].metadata["capability_result"] is None
            assert "Execution failed" in results[0].error
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_capability_executes_with_injected_backend(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        backend = FakeResearchBackend()
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            engine.adapters.unregister("research")
            research = ResearchAdapter(backend)
            await research.initialize()
            engine.adapters.register(research)

            result = await engine.execute_capability(
                "research",
                {"query": "JARVIS", "limit": 1},
            )
            assert result.success is True
            assert result.metadata["adapter"] == "research"
            assert result.data["query"] == "JARVIS"
            assert len(result.data["results"]) == 1
        finally:
            await engine.memory.store.close()


class TestResearchAuthorizationAndPolicy:
    """Authorization and policy remain enforced for research execution."""

    @pytest.mark.asyncio
    async def test_policy_denied_blocks_research(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(
            policy=PolicyEngine([PolicyRule(intent="research", allowed=False)])
        )
        try:
            await engine.adapters.initialize_all()
            with pytest.raises(PermissionError):
                await engine.execute_capability("research", {"query": "q"})
            with pytest.raises(PermissionError):
                await engine.execute_request("Research JARVIS")
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_missing_policy_rule_denies_research(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine([]))
        try:
            await engine.adapters.initialize_all()
            with pytest.raises(PermissionError):
                await engine.execute_capability("research", {"query": "q"})
        finally:
            await engine.memory.store.close()


class TestResearchLifecycleIntegration:
    """Events, recovery, and observability remain unchanged for research."""

    @pytest.mark.asyncio
    async def test_research_pipeline_publishes_request_events(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            started: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            completed: list[dict[str, Any]] = []

            async def on_started(payload: dict[str, Any]) -> None:
                started.append(payload)

            async def on_failed(payload: dict[str, Any]) -> None:
                failed.append(payload)

            async def on_completed(payload: dict[str, Any]) -> None:
                completed.append(payload)

            await engine.events.subscribe("request.started", on_started)
            await engine.events.subscribe("request.failed", on_failed)
            await engine.events.subscribe("request.completed", on_completed)

            await engine.execute_request("Research JARVIS")

            assert started == [{"objective": "Research JARVIS"}]
            assert failed == [{"objective": "Research JARVIS", "success": False}]
            assert completed == []
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_success_publishes_request_completed(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        backend = FakeResearchBackend()
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            engine.adapters.unregister("research")
            research = ResearchAdapter(backend)
            await research.initialize()
            engine.adapters.register(research)

            failed: list[dict[str, Any]] = []
            completed: list[dict[str, Any]] = []

            async def on_failed(payload: dict[str, Any]) -> None:
                failed.append(payload)

            async def on_completed(payload: dict[str, Any]) -> None:
                completed.append(payload)

            await engine.events.subscribe("request.failed", on_failed)
            await engine.events.subscribe("request.completed", on_completed)

            await engine.execute_request("Research JARVIS")

            assert failed == []
            assert completed == [
                {"objective": "Research JARVIS", "success": True}
            ]
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_capability_publishes_capability_events(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            capability_started: list[dict[str, Any]] = []
            capability_completed: list[dict[str, Any]] = []

            async def on_capability_started(payload: dict[str, Any]) -> None:
                capability_started.append(payload)

            async def on_capability_completed(payload: dict[str, Any]) -> None:
                capability_completed.append(payload)

            await engine.events.subscribe(
                "capability.execution.started", on_capability_started
            )
            await engine.events.subscribe(
                "capability.execution.completed", on_capability_completed
            )

            await engine.execute_capability("research", {"query": "JARVIS"})

            assert capability_started == [{"intent": "research"}]
            assert capability_completed == [
                {"intent": "research", "success": False}
            ]
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_execution_flows_through_recovery(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            original = engine.recovery.async_execute_with_recovery
            calls = 0

            async def tracking_recovery(operation, *args, **kwargs):
                nonlocal calls
                calls += 1
                return await original(operation, *args, **kwargs)

            engine.recovery.async_execute_with_recovery = tracking_recovery

            await engine.execute_request("Research JARVIS")

            assert calls == 1, "The recovery boundary must wrap research execution"
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_pipeline_records_observability(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            assert engine.is_observability_enabled is True

            await engine.execute_request("Research JARVIS")

            snapshot = engine.observability.snapshot()
            metrics = snapshot["metrics"]
            assert metrics["requests.started"]["value"] == 1
            assert metrics["requests.failed"]["value"] == 1
            assert metrics.get("requests.completed", {}).get("value", 0) == 0
        finally:
            await engine.memory.store.close()

    @pytest.mark.asyncio
    async def test_research_success_records_observability_completed(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setenv("JARVIS_STORAGE", str(tmp_path))
        backend = FakeResearchBackend()
        engine = Bootstrap().build(policy=PolicyEngine(list(RESEARCH_POLICY_RULES)))
        try:
            await engine.adapters.initialize_all()

            engine.adapters.unregister("research")
            research = ResearchAdapter(backend)
            await research.initialize()
            engine.adapters.register(research)

            await engine.execute_request("Research JARVIS")

            metrics = engine.observability.snapshot()["metrics"]
            assert metrics["requests.started"]["value"] == 1
            assert metrics["requests.completed"]["value"] == 1
            assert metrics.get("requests.failed", {}).get("value", 0) == 0
        finally:
            await engine.memory.store.close()


def test_research_result_contract() -> None:
    result = ResearchResult(
        title="t",
        snippet="s",
        url="u",
        source="src",
    )
    assert result.title == "t"
    assert result.snippet == "s"
    assert result.url == "u"
    assert result.source == "src"
