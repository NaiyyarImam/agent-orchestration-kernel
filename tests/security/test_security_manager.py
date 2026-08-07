"""Unit tests for SecurityManager."""

from __future__ import annotations

from kernel.security.security_manager import SecurityManager
import pytest


class TestAuthorize:
    """Tests for SecurityManager.authorize()."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_authorize_returns_true(self, manager: SecurityManager) -> None:
        result = await manager.authorize("user", "read", "file")
        assert result is True

    @pytest.mark.asyncio
    async def test_authorize_accepts_context(self, manager: SecurityManager) -> None:
        result = await manager.authorize(
            "user", "write", "file", context={"ip": "1.2.3.4", "role": "admin"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_authorize_creates_audit_event(self, manager: SecurityManager) -> None:
        await manager.authorize("user", "read", "file")
        log = manager.audit_log()
        assert len(log) == 1
        assert log[0]["event"] == "authorize"
        assert log[0]["details"]["subject"] == "user"
        assert log[0]["details"]["action"] == "read"
        assert log[0]["details"]["resource"] == "file"
        assert log[0]["details"]["allowed"] is True

    @pytest.mark.asyncio
    async def test_authorize_empty_strings(self, manager: SecurityManager) -> None:
        result = await manager.authorize("", "", "")
        assert result is True

    @pytest.mark.asyncio
    async def test_authorize_unicode_inputs(self, manager: SecurityManager) -> None:
        result = await manager.authorize("用户", "读取", "文件")
        assert result is True


class TestSandboxRequired:
    """Tests for SecurityManager.sandbox_required()."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_execute_code_requires_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("execute_code", "script.py") is True

    @pytest.mark.asyncio
    async def test_shell_command_requires_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("shell_command", "ls") is True

    @pytest.mark.asyncio
    async def test_filesystem_write_requires_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("filesystem_write", "/tmp/x") is True

    @pytest.mark.asyncio
    async def test_network_request_requires_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("network_request", "http://x") is True

    @pytest.mark.asyncio
    async def test_unknown_action_no_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("unknown", "x") is False

    @pytest.mark.asyncio
    async def test_read_no_sandbox(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("read", "file") is False

    @pytest.mark.asyncio
    async def test_resource_does_not_affect_result(self, manager: SecurityManager) -> None:
        assert await manager.sandbox_required("execute_code", "anything") is True
        assert await manager.sandbox_required("execute_code", "") is True
        assert await manager.sandbox_required("execute_code", None) is True  # type: ignore[arg-type]


class TestAudit:
    """Tests for SecurityManager.audit()."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_audit_creates_entry(self, manager: SecurityManager) -> None:
        await manager.audit("test_event", {"key": "value"})
        log = manager.audit_log()
        assert len(log) == 1

    @pytest.mark.asyncio
    async def test_audit_timestamp_exists(self, manager: SecurityManager) -> None:
        await manager.audit("test", {})
        log = manager.audit_log()
        assert "timestamp" in log[0]
        assert isinstance(log[0]["timestamp"], str)
        assert "T" in log[0]["timestamp"]  # ISO format

    @pytest.mark.asyncio
    async def test_audit_stores_event(self, manager: SecurityManager) -> None:
        await manager.audit("my_event", {})
        log = manager.audit_log()
        assert log[0]["event"] == "my_event"

    @pytest.mark.asyncio
    async def test_audit_stores_details(self, manager: SecurityManager) -> None:
        await manager.audit("test", {"k1": "v1", "k2": 42})
        log = manager.audit_log()
        assert log[0]["details"] == {"k1": "v1", "k2": 42}

    @pytest.mark.asyncio
    async def test_audit_multiple_entries_preserve_order(self, manager: SecurityManager) -> None:
        await manager.audit("first", {})
        await manager.audit("second", {})
        await manager.audit("third", {})
        log = manager.audit_log()
        assert [e["event"] for e in log] == ["first", "second", "third"]


class TestValidateTool:
    """Tests for SecurityManager.validate_tool()."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_empty_approved_list_allows_all(self, manager: SecurityManager) -> None:
        assert await manager.validate_tool("any_tool") is True
        assert await manager.validate_tool("another") is True

    @pytest.mark.asyncio
    async def test_approved_tool_allowed(self, manager: SecurityManager) -> None:
        manager.approve_tool("calculator")
        assert await manager.validate_tool("calculator") is True

    @pytest.mark.asyncio
    async def test_unapproved_tool_denied(self, manager: SecurityManager) -> None:
        manager.approve_tool("calculator")
        assert await manager.validate_tool("other") is False

    @pytest.mark.asyncio
    async def test_multiple_approved_tools(self, manager: SecurityManager) -> None:
        manager.approve_tool("tool_a")
        manager.approve_tool("tool_b")
        assert await manager.validate_tool("tool_a") is True
        assert await manager.validate_tool("tool_b") is True
        assert await manager.validate_tool("tool_c") is False


class TestHealthCheck:
    """Tests for SecurityManager.health_check()."""

    @pytest.fixture
    def manager(self) -> SecurityManager:
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self, manager: SecurityManager) -> None:
        assert await manager.health_check() is True


class TestApproveTool:
    """Tests for SecurityManager.approve_tool()."""

    def test_single_approval(self) -> None:
        manager = SecurityManager()
        manager.approve_tool("calc")
        assert "calc" in manager._approved_tools

    def test_duplicate_approval_idempotent(self) -> None:
        manager = SecurityManager()
        manager.approve_tool("calc")
        manager.approve_tool("calc")
        assert list(manager._approved_tools) == ["calc"]

    def test_multiple_approvals(self) -> None:
        manager = SecurityManager()
        manager.approve_tool("a")
        manager.approve_tool("b")
        manager.approve_tool("c")
        assert manager._approved_tools == {"a", "b", "c"}


class TestAuditLog:
    """Tests for SecurityManager.audit_log()."""

    def test_empty_log(self) -> None:
        manager = SecurityManager()
        assert manager.audit_log() == []

    def test_populated_log(self) -> None:
        manager = SecurityManager()
        import asyncio

        async def add_entries() -> None:
            await manager.audit("first", {})
            await manager.audit("second", {})

        asyncio.run(add_entries())
        log = manager.audit_log()
        assert len(log) == 2
        assert log[0]["event"] == "first"
        assert log[1]["event"] == "second"

    def test_returns_copy_not_internal_list(self) -> None:
        manager = SecurityManager()
        import asyncio

        async def add_entry() -> None:
            await manager.audit("test", {})

        asyncio.run(add_entry())
        log = manager.audit_log()
        log.clear()
        assert len(manager.audit_log()) == 1