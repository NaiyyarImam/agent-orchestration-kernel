"""Unit tests for ToolRegistry."""

from __future__ import annotations

import pytest

from kernel.tools.tool_registry import ToolRegistry


class DummyTool:
    """Simple tool used for registry testing."""

    def __init__(self, name: str) -> None:
        self.name = name


class ConfigurableTool:
    """Tool with configurable validation, invocation, and health behavior."""

    def __init__(
        self,
        name: str,
        description: str = "",
        validate_result: bool = True,
        invoke_result: object = "ok",
        health_result: bool = True,
    ) -> None:
        self.name = name
        self.description = description
        self._validate_result = validate_result
        self._invoke_result = invoke_result
        self._health_result = health_result
        self.validate_calls = 0
        self.invoke_calls = 0
        self.last_kwargs: dict = {}

    async def validate(self, **kwargs: object) -> bool:
        self.validate_calls += 1
        return self._validate_result

    async def invoke(self, **kwargs: object) -> object:
        self.invoke_calls += 1
        self.last_kwargs = dict(kwargs)
        return self._invoke_result

    async def health_check(self) -> bool:
        return self._health_result


def test_register_tool() -> None:
    registry = ToolRegistry()
    tool = DummyTool("calculator")

    registry.register(tool)

    assert registry.get("calculator") is tool


def test_register_multiple_tools() -> None:
    registry = ToolRegistry()

    registry.register(DummyTool("calculator"))
    registry.register(DummyTool("search"))

    assert registry.get("calculator").name == "calculator"
    assert registry.get("search").name == "search"


def test_duplicate_registration_overwrites_or_preserves() -> None:
    registry = ToolRegistry()

    first = DummyTool("calculator")
    second = DummyTool("calculator")

    registry.register(first)
    with pytest.raises(ValueError):
        registry.register(second)


def test_unknown_tool_raises_key_error() -> None:
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("does-not-exist")


class TestUnregister:
    """Tests for tool unregistration."""

    def test_unregister_existing_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))

        assert registry.unregister("calculator") is True
        assert registry.is_empty() is True

    def test_unregister_missing_tool_returns_false(self) -> None:
        registry = ToolRegistry()

        assert registry.unregister("missing") is False

    def test_unregister_removes_only_target(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))
        registry.register(DummyTool("search"))

        registry.unregister("calculator")

        assert registry.exists("calculator") is False
        assert registry.exists("search") is True


class TestListTools:
    """Tests for listing registered tools."""

    def test_list_tools_empty(self) -> None:
        registry = ToolRegistry()
        assert registry.list_tools() == []

    def test_list_tools_sorted(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("zeta"))
        registry.register(DummyTool("alpha"))
        registry.register(DummyTool("middle"))

        assert registry.list_tools() == ["alpha", "middle", "zeta"]


class TestToolInfo:
    """Tests for tool metadata retrieval."""

    def test_tool_info_includes_all_fields(self) -> None:
        registry = ToolRegistry()
        registry.register(ConfigurableTool("calculator", description="Performs math"))

        info = registry.tool_info("calculator")

        assert info == {
            "name": "calculator",
            "description": "Performs math",
            "type": "ConfigurableTool",
        }

    def test_tool_info_missing_description_defaults_empty(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("plain"))

        info = registry.tool_info("plain")

        assert info["name"] == "plain"
        assert info["description"] == ""
        assert info["type"] == "DummyTool"

    def test_tool_info_unknown_tool_raises(self) -> None:
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            registry.tool_info("does-not-exist")


class TestInvoke:
    """Tests for tool invocation."""

    @pytest.mark.asyncio
    async def test_invoke_success_returns_result(self) -> None:
        registry = ToolRegistry()
        tool = ConfigurableTool("calculator", invoke_result=42)
        registry.register(tool)

        result = await registry.invoke("calculator", a=1, b=2)

        assert result == 42
        assert tool.validate_calls == 1
        assert tool.invoke_calls == 1
        assert tool.last_kwargs == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_invoke_validation_failure_raises(self) -> None:
        registry = ToolRegistry()
        tool = ConfigurableTool("calculator", validate_result=False)
        registry.register(tool)

        with pytest.raises(ValueError, match="Validation failed"):
            await registry.invoke("calculator")

        assert tool.invoke_calls == 0

    @pytest.mark.asyncio
    async def test_invoke_unknown_tool_raises(self) -> None:
        registry = ToolRegistry()

        with pytest.raises(KeyError):
            await registry.invoke("does-not-exist")


class TestHealthCheck:
    """Tests for registry health checking."""

    @pytest.mark.asyncio
    async def test_health_check_empty_registry_is_healthy(self) -> None:
        registry = ToolRegistry()
        assert await registry.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_all_tools_healthy(self) -> None:
        registry = ToolRegistry()
        registry.register(ConfigurableTool("a", health_result=True))
        registry.register(ConfigurableTool("b", health_result=True))

        assert await registry.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_one_unhealthy_tool_fails(self) -> None:
        registry = ToolRegistry()
        registry.register(ConfigurableTool("a", health_result=True))
        registry.register(ConfigurableTool("b", health_result=False))

        assert await registry.health_check() is False


class TestRegistryInfo:
    """Tests for runtime registry information."""

    @pytest.mark.asyncio
    async def test_registry_info_empty(self) -> None:
        registry = ToolRegistry()

        info = await registry.registry_info()

        assert info == {
            "healthy": True,
            "tool_count": 0,
            "tools": [],
        }

    @pytest.mark.asyncio
    async def test_registry_info_with_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(ConfigurableTool("calculator"))
        registry.register(ConfigurableTool("search"))

        info = await registry.registry_info()

        assert info["healthy"] is True
        assert info["tool_count"] == 2
        assert info["tools"] == ["calculator", "search"]


class TestExists:
    """Tests for the exists method."""

    def test_exists_registered_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))

        assert registry.exists("calculator") is True

    def test_exists_missing_tool(self) -> None:
        registry = ToolRegistry()

        assert registry.exists("calculator") is False


class TestClear:
    """Tests for clearing the registry."""

    def test_clear_empties_registry(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))
        registry.register(DummyTool("search"))

        registry.clear()

        assert registry.is_empty() is True
        assert registry.count == 0
        assert registry.list_tools() == []

    def test_clear_after_unregister(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))

        registry.unregister("calculator")
        registry.clear()

        assert registry.is_empty() is True


class TestIsEmpty:
    """Tests for the is_empty method."""

    def test_is_empty_initial_registry(self) -> None:
        registry = ToolRegistry()
        assert registry.is_empty() is True

    def test_is_empty_after_register(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))

        assert registry.is_empty() is False

    def test_is_empty_after_unregister_all(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))

        registry.unregister("calculator")

        assert registry.is_empty() is True


class TestCount:
    """Tests for the count property."""

    def test_count_initial_registry(self) -> None:
        registry = ToolRegistry()
        assert registry.count == 0

    def test_count_increments_on_register(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))
        registry.register(DummyTool("search"))

        assert registry.count == 2

    def test_count_decrements_on_unregister(self) -> None:
        registry = ToolRegistry()
        registry.register(DummyTool("calculator"))
        registry.register(DummyTool("search"))

        registry.unregister("calculator")

        assert registry.count == 1
