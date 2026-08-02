"""Unit tests for CapabilityAdapterManager."""

from __future__ import annotations

import asyncio

import pytest

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.interfaces.capability_adapter import CapabilityAdapter
from kernel.interfaces.capability_adapter import CapabilityResult
from kernel.interfaces.capability_adapter import CapabilityTask


class DummyAdapter(CapabilityAdapter):
    """Simple adapter used for registry testing."""

    def __init__(
        self,
        name: str,
        capability_type: str = "test",
        description: str = "Test adapter",
        supports_intent: str = "test",
    ) -> None:
        self._name = name
        self._capability_type = capability_type
        self._description = description
        self._supports_intent = supports_intent
        self.initialized = False
        self.shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def capability_type(self) -> str:
        return self._capability_type

    @property
    def description(self) -> str:
        return self._description

    def supports(self, intent: str) -> bool:
        return intent == self._supports_intent

    async def initialize(self) -> None:
        self.initialized = True

    async def health_check(self) -> bool:
        return True

    async def execute(self, task: CapabilityTask) -> CapabilityResult:
        return CapabilityResult(success=True, data=f"executed {self._name}")

    async def shutdown(self) -> None:
        self.shutdown_called = True


class FailingHealthAdapter(DummyAdapter):
    """Adapter that fails health checks."""

    async def health_check(self) -> bool:
        return False


class FailingInitAdapter(DummyAdapter):
    """Adapter that fails initialization."""

    async def initialize(self) -> None:
        raise RuntimeError("init failed")


def test_register_adapter() -> None:
    manager = CapabilityAdapterManager()
    adapter = DummyAdapter("coding")

    manager.register(adapter)

    assert manager.get("coding") is adapter


def test_register_multiple_adapters() -> None:
    manager = CapabilityAdapterManager()

    manager.register(DummyAdapter("coding"))
    manager.register(DummyAdapter("research"))

    assert manager.get("coding").name == "coding"
    assert manager.get("research").name == "research"


def test_duplicate_adapter_registration_raises() -> None:
    manager = CapabilityAdapterManager()

    manager.register(DummyAdapter("coding"))

    with pytest.raises(ValueError):
        manager.register(DummyAdapter("coding"))


def test_unknown_adapter_raises_key_error() -> None:
    manager = CapabilityAdapterManager()

    with pytest.raises(KeyError):
        manager.get("does-not-exist")


# --- New tests for uncovered public methods ---


def test_unregister_existing_adapter() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding"))

    result = manager.unregister("coding")

    assert result is True
    assert not manager.exists("coding")


def test_unregister_unknown_adapter_returns_false() -> None:
    manager = CapabilityAdapterManager()

    result = manager.unregister("missing")

    assert result is False


def test_exists_before_and_after_registration() -> None:
    manager = CapabilityAdapterManager()

    assert manager.exists("coding") is False

    manager.register(DummyAdapter("coding"))

    assert manager.exists("coding") is True


def test_can_handle_uses_intent_support_not_adapter_name() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    assert manager.can_handle("code") is True
    assert manager.can_handle("coding") is False


def test_can_handle_unknown_intent_is_false() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    assert manager.can_handle("does-not-exist") is False


def test_can_handle_empty_registry_is_false() -> None:
    manager = CapabilityAdapterManager()

    assert manager.can_handle("code") is False


def test_can_handle_matches_execute_routing() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    assert manager.can_handle("code") is True
    assert (
        asyncio.run(
            manager.execute(CapabilityTask(task_id="t1", intent="code"))
        ).success
        is True
    )


def test_list_adapters_returns_sorted_names() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("zebra"))
    manager.register(DummyAdapter("alpha"))
    manager.register(DummyAdapter("beta"))

    names = manager.list_adapters()

    assert names == ["alpha", "beta", "zebra"]


def test_list_adapters_empty_when_no_adapters() -> None:
    manager = CapabilityAdapterManager()

    assert manager.list_adapters() == []


def test_count_reflects_registrations_and_removals() -> None:
    manager = CapabilityAdapterManager()

    assert manager.count == 0

    manager.register(DummyAdapter("coding"))
    assert manager.count == 1

    manager.register(DummyAdapter("research"))
    assert manager.count == 2

    manager.unregister("coding")
    assert manager.count == 1

    manager.clear()
    assert manager.count == 0


def test_clear_removes_all_adapters() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding"))
    manager.register(DummyAdapter("research"))

    manager.clear()

    assert manager.count == 0
    assert manager.list_adapters() == []


def test_find_adapter_for_intent_returns_correct_adapter() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))
    manager.register(DummyAdapter("research", supports_intent="search"))

    adapter = manager.find_adapter_for_intent("code")

    assert adapter.name == "coding"


def test_find_adapter_for_intent_raises_when_no_match() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    with pytest.raises(KeyError, match="No adapter supports intent: search"):
        manager.find_adapter_for_intent("search")


def test_execute_delegates_to_selected_adapter() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    task = CapabilityTask(task_id="1", intent="code", payload={"data": "test"})

    result = asyncio.run(manager.execute(task))

    assert result.success is True
    assert result.data == "executed coding"


def test_execute_raises_when_no_adapter_supports_intent() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding", supports_intent="code"))

    task = CapabilityTask(task_id="1", intent="unknown")

    with pytest.raises(KeyError, match="No adapter supports intent: unknown"):
        asyncio.run(manager.execute(task))


def test_health_check_returns_true_when_empty() -> None:
    manager = CapabilityAdapterManager()

    assert asyncio.run(manager.health_check()) is True


def test_health_check_returns_true_when_all_healthy() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding"))
    manager.register(DummyAdapter("research"))

    assert asyncio.run(manager.health_check()) is True


def test_health_check_returns_false_when_any_unhealthy() -> None:
    manager = CapabilityAdapterManager()
    manager.register(DummyAdapter("coding"))
    manager.register(FailingHealthAdapter("research"))

    assert asyncio.run(manager.health_check()) is False


def test_initialize_all_calls_initialize_on_each_adapter() -> None:
    manager = CapabilityAdapterManager()
    adapter1 = DummyAdapter("coding")
    adapter2 = DummyAdapter("research")
    manager.register(adapter1)
    manager.register(adapter2)

    asyncio.run(manager.initialize_all())

    assert adapter1.initialized is True
    assert adapter2.initialized is True


def test_initialize_all_propagates_exception() -> None:
    manager = CapabilityAdapterManager()
    manager.register(FailingInitAdapter("coding"))

    with pytest.raises(RuntimeError, match="init failed"):
        asyncio.run(manager.initialize_all())


def test_shutdown_all_calls_shutdown_on_each_adapter() -> None:
    manager = CapabilityAdapterManager()
    adapter1 = DummyAdapter("coding")
    adapter2 = DummyAdapter("research")
    manager.register(adapter1)
    manager.register(adapter2)

    asyncio.run(manager.shutdown_all())

    assert adapter1.shutdown_called is True
    assert adapter2.shutdown_called is True
