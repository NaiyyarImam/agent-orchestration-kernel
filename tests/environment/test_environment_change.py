

from datetime import datetime

from kernel.environment.environment_change import ChangeType, EnvironmentChange


def test_default_environment_change() -> None:
    change = EnvironmentChange(
        change_type=ChangeType.CUSTOM,
        description="Test change",
        source="unit-test",
    )

    assert change.change_type is ChangeType.CUSTOM
    assert change.description == "Test change"
    assert change.source == "unit-test"
    assert isinstance(change.change_id, str)
    assert isinstance(change.timestamp, datetime)
    assert change.metadata == {}


def test_custom_environment_change() -> None:
    change = EnvironmentChange(
        change_type=ChangeType.CPU_SPIKE,
        description="CPU exceeded threshold",
        source="monitor",
        metadata={"cpu": 95.2},
    )

    assert change.change_type is ChangeType.CPU_SPIKE
    assert change.metadata == {"cpu": 95.2}


def test_environment_change_to_dict() -> None:
    change = EnvironmentChange(
        change_type=ChangeType.ADAPTER_OFFLINE,
        description="Coding adapter disconnected",
        source="adapter-manager",
    )

    data = change.to_dict()

    assert data["change_id"] == change.change_id
    assert data["change_type"] == "adapter_offline"
    assert data["description"] == "Coding adapter disconnected"
    assert data["source"] == "adapter-manager"
    assert data["metadata"] == {}
    assert isinstance(data["timestamp"], str)


def test_change_ids_are_unique() -> None:
    first = EnvironmentChange(ChangeType.CUSTOM, "A", "test")
    second = EnvironmentChange(ChangeType.CUSTOM, "B", "test")

    assert first.change_id != second.change_id


def test_environment_change_is_immutable() -> None:
    change = EnvironmentChange(ChangeType.CUSTOM, "Immutable", "test")

    try:
        change.description = "Modified"
        assert False, "EnvironmentChange should be immutable"
    except AttributeError:
        pass