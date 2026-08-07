"""Tests for the application entry point health rendering."""

from __future__ import annotations

from main import _status_label, render_health


class TestStatusLabel:
    """Tests for the health status label helper."""

    def test_true_boolean_is_ok(self) -> None:
        assert _status_label(True) == "OK"

    def test_false_boolean_is_failed(self) -> None:
        assert _status_label(False) == "FAILED"

    def test_nested_dict_all_healthy_is_ok(self) -> None:
        assert _status_label({"healthy": True}) == "OK"

    def test_nested_dict_any_unhealthy_is_failed(self) -> None:
        assert _status_label({"healthy": True, "unhealthy": False}) == "FAILED"

    def test_empty_nested_dict_is_failed(self) -> None:
        assert _status_label({}) == "FAILED"


class TestRenderHealth:
    """Tests for the entry point health rendering."""

    def test_renders_boolean_components(self) -> None:
        lines = render_health({"memory": True, "tools": False})

        assert lines == ["memory         OK", "tools          FAILED"]

    def test_renders_nested_health_with_overall_status(self) -> None:
        lines = render_health(
            {
                "memory": True,
                "models": {"llama3": True, "mistral": False},
            }
        )

        assert "memory         OK" in lines
        assert "models         FAILED" in lines
        assert "  llama3       OK" in lines
        assert "  mistral      FAILED" in lines

    def test_nested_all_healthy_reports_ok(self) -> None:
        lines = render_health({"models": {"llama3": True}})

        assert "models         OK" in lines
        assert "  llama3       OK" in lines

    def test_empty_health_renders_no_lines(self) -> None:
        assert render_health({}) == []
