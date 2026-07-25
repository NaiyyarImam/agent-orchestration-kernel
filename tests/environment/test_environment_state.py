

from kernel.environment.environment_snapshot import EnvironmentSnapshot
from kernel.environment.environment_state import EnvironmentState


def test_default_state_contains_snapshot() -> None:
    state = EnvironmentState()

    snapshot = state.get_snapshot()

    assert isinstance(snapshot, EnvironmentSnapshot)
    assert snapshot == state.current_snapshot


def test_update_replaces_snapshot() -> None:
    state = EnvironmentState()

    new_snapshot = EnvironmentSnapshot(cpu_usage=55.5, memory_usage=70.0)

    state.update(new_snapshot)

    assert state.get_snapshot() is new_snapshot
    assert state.current_snapshot is new_snapshot


def test_multiple_updates_keep_latest_snapshot() -> None:
    state = EnvironmentState()

    first = EnvironmentSnapshot(cpu_usage=10.0)
    second = EnvironmentSnapshot(cpu_usage=20.0)

    state.update(first)
    state.update(second)

    assert state.get_snapshot() is second
    assert state.get_snapshot().cpu_usage == 20.0


def test_get_snapshot_returns_current_snapshot() -> None:
    snapshot = EnvironmentSnapshot(memory_usage=33.3)
    state = EnvironmentState(current_snapshot=snapshot)

    assert state.get_snapshot() is snapshot


def test_update_preserves_snapshot_instance() -> None:
    state = EnvironmentState()
    snapshot = EnvironmentSnapshot(active_models=("qwen3:14b",))

    state.update(snapshot)

    assert state.current_snapshot is snapshot