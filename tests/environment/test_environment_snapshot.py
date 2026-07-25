

from datetime import datetime

from kernel.environment.environment_snapshot import EnvironmentSnapshot


def test_default_snapshot_values() -> None:
    snapshot = EnvironmentSnapshot()

    assert snapshot.cpu_usage == 0.0
    assert snapshot.memory_usage == 0.0
    assert snapshot.active_models == ()
    assert snapshot.active_plugins == ()
    assert snapshot.running_workflows == ()
    assert snapshot.adapter_status == {}
    assert snapshot.metadata == {}
    assert isinstance(snapshot.snapshot_id, str)
    assert isinstance(snapshot.timestamp, datetime)


def test_custom_snapshot_values() -> None:
    snapshot = EnvironmentSnapshot(
        cpu_usage=42.5,
        memory_usage=67.8,
        active_models=("qwen3:14b",),
        active_plugins=("planner",),
        running_workflows=("research",),
        adapter_status={"coding": "online"},
        metadata={"source": "test"},
    )

    assert snapshot.cpu_usage == 42.5
    assert snapshot.memory_usage == 67.8
    assert snapshot.active_models == ("qwen3:14b",)
    assert snapshot.active_plugins == ("planner",)
    assert snapshot.running_workflows == ("research",)
    assert snapshot.adapter_status == {"coding": "online"}
    assert snapshot.metadata == {"source": "test"}


def test_snapshot_to_dict() -> None:
    snapshot = EnvironmentSnapshot(cpu_usage=10.0)

    data = snapshot.to_dict()

    assert data["snapshot_id"] == snapshot.snapshot_id
    assert data["cpu_usage"] == 10.0
    assert data["memory_usage"] == 0.0
    assert data["active_models"] == []
    assert data["active_plugins"] == []
    assert data["running_workflows"] == []
    assert data["adapter_status"] == {}
    assert data["metadata"] == {}
    assert isinstance(data["timestamp"], str)


def test_snapshot_ids_are_unique() -> None:
    first = EnvironmentSnapshot()
    second = EnvironmentSnapshot()

    assert first.snapshot_id != second.snapshot_id


def test_snapshot_is_immutable() -> None:
    snapshot = EnvironmentSnapshot()

    try:
        snapshot.cpu_usage = 99.0
        assert False, "EnvironmentSnapshot should be immutable"
    except AttributeError:
        pass