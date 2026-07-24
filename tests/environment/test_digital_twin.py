

from kernel.environment.digital_twin import DigitalTwin
from kernel.environment.environment_change import ChangeType, EnvironmentChange
from kernel.environment.environment_snapshot import EnvironmentSnapshot


def test_default_digital_twin() -> None:
    twin = DigitalTwin()

    assert isinstance(twin.get_snapshot(), EnvironmentSnapshot)
    assert twin.get_changes() == []


def test_update_snapshot() -> None:
    twin = DigitalTwin()
    snapshot = EnvironmentSnapshot(cpu_usage=88.8)

    returned = twin.update(snapshot)

    assert returned is snapshot
    assert twin.get_snapshot() is snapshot


def test_record_change() -> None:
    twin = DigitalTwin()
    change = EnvironmentChange(ChangeType.CUSTOM, "Test", "unit-test")

    twin.record_change(change)

    changes = twin.get_changes()
    assert len(changes) == 1
    assert changes[0] is change


def test_clear_changes() -> None:
    twin = DigitalTwin()

    twin.record_change(EnvironmentChange(ChangeType.CUSTOM, "One", "test"))
    twin.record_change(EnvironmentChange(ChangeType.CUSTOM, "Two", "test"))

    assert len(twin.get_changes()) == 2

    twin.clear_changes()

    assert twin.get_changes() == []


def test_get_changes_returns_copy() -> None:
    twin = DigitalTwin()
    twin.record_change(EnvironmentChange(ChangeType.CUSTOM, "Only", "test"))

    changes = twin.get_changes()
    changes.clear()

    assert changes == []
    assert len(twin.get_changes()) == 1