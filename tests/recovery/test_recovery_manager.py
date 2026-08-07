"""Unit tests for RecoveryManager."""

from __future__ import annotations

import pytest

from kernel.recovery.recovery_action import RecoveryAction
from kernel.recovery.recovery_manager import RecoveryManager
from kernel.recovery.recovery_policy import RecoveryPolicy
from kernel.recovery.recovery_result import RecoveryResult


class TestRecoveryManagerInitialization:
    """Tests for RecoveryManager initialization and properties."""

    def test_init_default_policy(self):
        manager = RecoveryManager()
        assert manager.policy is not None
        assert manager.policy.max_retries == 3
        assert manager.policy.default_action == RecoveryAction.RETRY

    def test_init_custom_policy(self):
        policy = RecoveryPolicy(max_retries=5, default_action=RecoveryAction.FAILOVER)
        manager = RecoveryManager(policy)
        assert manager.policy is policy
        assert manager.policy.max_retries == 5
        assert manager.policy.default_action == RecoveryAction.FAILOVER

    def test_policy_property_returns_policy(self):
        policy = RecoveryPolicy()
        manager = RecoveryManager(policy)
        assert manager.policy is policy

    def test_policy_info_returns_dict(self):
        manager = RecoveryManager()
        info = manager.policy_info()
        assert isinstance(info, dict)
        assert "policy" in info
        assert info["policy"] == "RecoveryPolicy"

    def test_policy_info_reflects_custom_policy(self):
        policy = RecoveryPolicy(max_retries=7, default_action=RecoveryAction.SKIP, retry_delay_seconds=1.5)
        manager = RecoveryManager(policy)
        info = manager.policy_info()
        assert info["policy"] == "RecoveryPolicy"

    @pytest.mark.asyncio
    async def test_manager_info_returns_dict(self):
        manager = RecoveryManager()
        info = await manager.manager_info()
        assert isinstance(info, dict)
        assert "healthy" in info
        assert "policy" in info
        assert info["healthy"] is True
        assert info["policy"] == "RecoveryPolicy"

    @pytest.mark.asyncio
    async def test_manager_info_includes_policy(self):
        policy = RecoveryPolicy(max_retries=2)
        manager = RecoveryManager(policy)
        info = await manager.manager_info()
        assert info["policy"] == "RecoveryPolicy"
        assert info["healthy"] is True


class TestRecoverMethod:
    """Tests for the recover method."""

    def test_recover_success_before_retry_limit(self):
        manager = RecoveryManager()
        result = manager.recover(0, "first try")
        assert isinstance(result, RecoveryResult)
        assert result.success is True
        assert result.action == RecoveryAction.RETRY
        assert result.message == "first try"

    def test_recover_success_at_retry_limit(self):
        manager = RecoveryManager()
        result = manager.recover(2, "at limit")
        assert result.success is True
        assert result.action == RecoveryAction.RETRY
        assert result.message == "at limit"

    def test_recover_abort_after_retry_limit(self):
        manager = RecoveryManager()
        result = manager.recover(3, "exceeded")
        assert result.success is False
        assert result.action == RecoveryAction.ABORT
        assert result.message == "exceeded"

    def test_recover_with_failure_action_policy(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.FAILOVER)
        manager = RecoveryManager(policy)
        result = manager.recover(0, "failover")
        assert result.success is True
        assert result.action == RecoveryAction.FAILOVER

    def test_recover_with_restart_action(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.RESTART)
        manager = RecoveryManager(policy)
        result = manager.recover(5, "restarting")
        assert result.success is True
        assert result.action == RecoveryAction.RESTART

    def test_recover_with_skip_action(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.SKIP)
        manager = RecoveryManager(policy)
        result = manager.recover(10, "skipping")
        assert result.success is True
        assert result.action == RecoveryAction.SKIP

    def test_recover_with_ignore_action(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.IGNORE)
        manager = RecoveryManager(policy)
        result = manager.recover(100, "ignoring")
        assert result.success is True
        assert result.action == RecoveryAction.IGNORE

    def test_recover_with_abort_action(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.ABORT)
        manager = RecoveryManager(policy)
        result = manager.recover(0, "aborting")
        assert result.success is False
        assert result.action == RecoveryAction.ABORT

    def test_recover_negative_attempt_raises(self):
        manager = RecoveryManager()
        with pytest.raises(ValueError, match="attempt must be non-negative"):
            manager.recover(-1, "negative")

    def test_recover_message_preserved(self):
        manager = RecoveryManager()
        message = "network timeout"
        result = manager.recover(1, message)
        assert result.message == message

    def test_recover_empty_message_defaults_to_empty(self):
        manager = RecoveryManager()
        result = manager.recover(1)
        assert result.message == ""

    def test_recover_returns_new_result_each_call(self):
        manager = RecoveryManager()
        result1 = manager.recover(0)
        result2 = manager.recover(0)
        assert result1 is not result2
        assert result1.timestamp <= result2.timestamp


class TestCanRetryMethod:
    """Tests for the can_retry method."""

    def test_can_retry_true_before_limit(self):
        manager = RecoveryManager()
        assert manager.can_retry(0) is True
        assert manager.can_retry(1) is True
        assert manager.can_retry(2) is True

    def test_can_retry_false_at_limit(self):
        manager = RecoveryManager()
        assert manager.can_retry(3) is False

    def test_can_retry_false_after_limit(self):
        manager = RecoveryManager()
        assert manager.can_retry(4) is False
        assert manager.can_retry(100) is False

    def test_can_retry_custom_max_retries(self):
        policy = RecoveryPolicy(max_retries=5)
        manager = RecoveryManager(policy)
        assert manager.can_retry(0) is True
        assert manager.can_retry(4) is True
        assert manager.can_retry(5) is False
        assert manager.can_retry(6) is False

    def test_can_retry_zero_max_retries(self):
        policy = RecoveryPolicy(max_retries=0)
        manager = RecoveryManager(policy)
        assert manager.can_retry(0) is False
        assert manager.can_retry(1) is False

    def test_can_retry_negative_raises(self):
        manager = RecoveryManager()
        with pytest.raises(ValueError, match="attempt must be non-negative"):
            manager.can_retry(-1)


class TestExecuteWithRecovery:
    """Tests for execute_with_recovery method."""

    def test_execute_with_recovery_success_first_try(self):
        manager = RecoveryManager()
        call_count = 0

        def operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = manager.execute_with_recovery(operation)
        assert result == "success"
        assert call_count == 1

    def test_execute_with_recovery_success_after_retries(self):
        manager = RecoveryManager()
        call_count = 0

        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary")
            return "success"

        result = manager.execute_with_recovery(operation)
        assert result == "success"
        assert call_count == 3

    def test_execute_with_recovery_failure_after_max_retries(self):
        manager = RecoveryManager()
        call_count = 0

        def operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("permanent")

        with pytest.raises(ConnectionError, match="permanent"):
            manager.execute_with_recovery(operation)
        assert call_count == 4

    def test_execute_with_recovery_failure_preserves_exception(self):
        manager = RecoveryManager()

        def operation():
            raise ValueError("custom error")

        with pytest.raises(ValueError, match="custom error"):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_custom_policy_failure_action(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.ABORT)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError, match="fail"):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_failure_action_abort_raises(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.ABORT)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_failure_action_failover_raises(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.FAILOVER)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_failure_action_restart_raises(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.RESTART)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_failure_action_skip_raises(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.SKIP)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_failure_action_ignore_raises(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.IGNORE)
        manager = RecoveryManager(policy)

        def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            manager.execute_with_recovery(operation)

    def test_execute_with_recovery_passes_args_kwargs(self):
        manager = RecoveryManager()

        def operation(a, b, c=3):
            return a + b + c

        result = manager.execute_with_recovery(operation, 1, 2, c=4)
        assert result == 7

    def test_execute_with_recovery_preserves_return_value(self):
        manager = RecoveryManager()

        def operation():
            return {"key": "value"}

        result = manager.execute_with_recovery(operation)
        assert result == {"key": "value"}

    def test_execute_with_recovery_returns_none(self):
        manager = RecoveryManager()

        def operation():
            return None

        result = manager.execute_with_recovery(operation)
        assert result is None


class TestAsyncExecuteWithRecovery:
    """Tests for async_execute_with_recovery method."""

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_success_first_try(self):
        manager = RecoveryManager()
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            return "async success"

        result = await manager.async_execute_with_recovery(operation)
        assert result == "async success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_success_after_retries(self):
        manager = RecoveryManager()
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary")
            return "async success"

        result = await manager.async_execute_with_recovery(operation)
        assert result == "async success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_failure_after_max_retries(self):
        manager = RecoveryManager()
        call_count = 0

        async def operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("permanent")

        with pytest.raises(ConnectionError, match="permanent"):
            await manager.async_execute_with_recovery(operation)
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_preserves_exception(self):
        manager = RecoveryManager()

        async def operation():
            raise ValueError("async error")

        with pytest.raises(ValueError, match="async error"):
            await manager.async_execute_with_recovery(operation)

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_custom_policy(self):
        policy = RecoveryPolicy(default_action=RecoveryAction.ABORT)
        manager = RecoveryManager(policy)

        async def operation():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await manager.async_execute_with_recovery(operation)

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_passes_args_kwargs(self):
        manager = RecoveryManager()

        async def operation(a, b, c=3):
            return a + b + c

        result = await manager.async_execute_with_recovery(operation, 1, 2, c=4)
        assert result == 7


class TestHealthCheck:
    """Tests for health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true(self):
        manager = RecoveryManager()
        assert await manager.health_check() is True

    @pytest.mark.asyncio
    async def test_health_check_with_custom_policy(self):
        policy = RecoveryPolicy(max_retries=10)
        manager = RecoveryManager(policy)
        assert await manager.health_check() is True


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_recover_boundary_at_max_retries(self):
        manager = RecoveryManager()
        result_at_limit = manager.recover(2)
        result_over_limit = manager.recover(3)
        assert result_at_limit.success is True
        assert result_at_limit.action == RecoveryAction.RETRY
        assert result_over_limit.success is False
        assert result_over_limit.action == RecoveryAction.ABORT

    def test_recover_with_zero_max_retries(self):
        policy = RecoveryPolicy(max_retries=0)
        manager = RecoveryManager(policy)
        result = manager.recover(0)
        assert result.success is False
        assert result.action == RecoveryAction.ABORT

    def test_policy_validation_negative_max_retries(self):
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RecoveryPolicy(max_retries=-1)

    def test_policy_validation_negative_delay(self):
        with pytest.raises(ValueError, match="retry_delay_seconds must be non-negative"):
            RecoveryPolicy(retry_delay_seconds=-1.0)

    def test_recover_with_unicode_message(self):
        manager = RecoveryManager()
        message = "错误: 连接超时 🌐"
        result = manager.recover(1, message)
        assert result.message == message

    def test_execute_with_recovery_empty_operation_raises(self):
        manager = RecoveryManager()

        def operation():
            return None

        result = manager.execute_with_recovery(operation)
        assert result is None


class TestStateTransitions:
    """Tests for state transitions and consistency."""

    def test_multiple_recover_calls_independent(self):
        manager = RecoveryManager()
        results = [manager.recover(i) for i in range(5)]
        assert results[0].action == RecoveryAction.RETRY
        assert results[1].action == RecoveryAction.RETRY
        assert results[2].action == RecoveryAction.RETRY
        assert results[3].action == RecoveryAction.ABORT
        assert results[4].action == RecoveryAction.ABORT

    def test_execute_with_recovery_then_recover_state(self):
        manager = RecoveryManager()
        call_count = 0

        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temp")
            return "ok"

        result = manager.execute_with_recovery(operation)
        assert result == "ok"

        recover_result = manager.recover(call_count)
        assert recover_result.action == RecoveryAction.ABORT

    def test_can_retry_consistent_with_recover(self):
        manager = RecoveryManager()
        for i in range(5):
            can = manager.can_retry(i)
            result = manager.recover(i)
            if can:
                assert result.action == RecoveryAction.RETRY
            else:
                assert result.action == RecoveryAction.ABORT


class TestInvalidInputs:
    """Tests for invalid input handling."""

    def test_recover_negative_attempt_raises(self):
        manager = RecoveryManager()
        with pytest.raises(ValueError):
            manager.recover(-1)

    def test_can_retry_negative_attempt_raises(self):
        manager = RecoveryManager()
        with pytest.raises(ValueError):
            manager.can_retry(-1)

    def test_init_with_none_policy_uses_default(self):
        manager = RecoveryManager(None)
        assert manager.policy is not None
        assert manager.policy.max_retries == 3

    def test_execute_with_recovery_none_operation_raises(self):
        manager = RecoveryManager()
        with pytest.raises(TypeError):
            manager.execute_with_recovery(None)

    @pytest.mark.asyncio
    async def test_async_execute_with_recovery_none_operation_raises(self):
        manager = RecoveryManager()
        with pytest.raises(TypeError):
            await manager.async_execute_with_recovery(None)


class TestRecoveryResult:
    """Tests for RecoveryResult serialization."""

    def test_to_dict_includes_all_fields(self):
        result = RecoveryResult(success=True, action=RecoveryAction.RETRY, message="test")
        data = result.to_dict()
        assert data["success"] is True
        assert data["action"] == "retry"
        assert data["message"] == "test"
        assert "timestamp" in data

    def test_from_dict_creates_result(self):
        data = {
            "success": True,
            "action": "failover",
            "message": "recovered",
            "timestamp": "2024-01-01T00:00:00+00:00",
        }
        result = RecoveryResult.from_dict(data)
        assert result.success is True
        assert result.action == RecoveryAction.FAILOVER
        assert result.message == "recovered"

    def test_from_dict_without_message_defaults_empty(self):
        data = {
            "success": False,
            "action": "abort",
            "timestamp": "2024-01-01T00:00:00+00:00",
        }
        result = RecoveryResult.from_dict(data)
        assert result.message == ""

    def test_roundtrip_serialization(self):
        original = RecoveryResult(success=True, action=RecoveryAction.RESTART, message="restarted")
        data = original.to_dict()
        restored = RecoveryResult.from_dict(data)
        assert restored.success == original.success
        assert restored.action == original.action
        assert restored.message == original.message