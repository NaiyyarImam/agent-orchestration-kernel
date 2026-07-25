

"""Unit tests for ToolRegistry."""

from __future__ import annotations

import pytest

from kernel.tools.tool_registry import ToolRegistry


class DummyTool:
    """Simple tool used for registry testing."""

    def __init__(self, name: str) -> None:
        self.name = name


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