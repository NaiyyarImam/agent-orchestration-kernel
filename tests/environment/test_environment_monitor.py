

from kernel.environment.environment_change import ChangeType, EnvironmentChange
from kernel.environment.environment_monitor import EnvironmentMonitor
from kernel.environment.environment_snapshot import EnvironmentSnapshot


def test_default_monitor_state() -> None:
    monitor = EnvironmentMonitor()

    assert isinstance(monitor.get_current_snapshot(), EnvironmentSnapshot)
    assert monitor.get_changes() == []


def test_capture_snapshot_updates_state() -> None:
    monitor = EnvironmentMonitor()
    snapshot = EnvironmentSnapshot(cpu_usage=75.0)

    returned = monitor.capture_snapshot(snapshot)

    assert returned is snapshot
    assert monitor.get_current_snapshot() is snapshot


def test_record_multiple_changes() -> None:
    monitor = EnvironmentMonitor()

    first = EnvironmentChange(ChangeType.CUSTOM, "First", "test")
    second = EnvironmentChange(ChangeType.CPU_SPIKE, "CPU high", "monitor")

    monitor.record_change(first)
    monitor.record_change(second)

    changes = monitor.get_changes()

    assert len(changes) == 2
    assert changes[0] is first
    assert changes[1] is second


def test_get_changes_returns_copy() -> None:
    monitor = EnvironmentMonitor()
    change = EnvironmentChange(ChangeType.CUSTOM, "Only", "test")

    monitor.record_change(change)

    changes = monitor.get_changes()
    changes.clear()

    assert len(changes) == 0
    assert len(monitor.get_changes()) == 1


def test_clear_changes() -> None:
    monitor = EnvironmentMonitor()

    monitor.record_change(EnvironmentChange(ChangeType.CUSTOM, "One", "test"))
    monitor.record_change(EnvironmentChange(ChangeType.CUSTOM, "Two", "test"))

    monitor.clear_changes()

    assert monitor.get_changes() == []