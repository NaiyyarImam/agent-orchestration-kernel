"""Unit tests for StorageManager."""

from __future__ import annotations

import json
import os
import shutil
import pytest

from kernel.storage.storage_manager import StorageManager


class TestStorageManagerInitialization:
    """Tests for StorageManager initialization and properties."""

    def test_init_creates_root_directory(self, tmp_path):
        storage = StorageManager(tmp_path / "storage")
        assert storage.root.exists()
        assert storage.root.is_dir()
        assert storage.root == (tmp_path / "storage").resolve()

    def test_init_expands_user_path(self, tmp_path):
        user_path = tmp_path / "~" / "storage"
        user_path.mkdir(parents=True)
        storage = StorageManager(user_path)
        assert storage.root == user_path.resolve()

    def test_init_resolves_relative_path(self, tmp_path):
        storage = StorageManager("storage")
        assert storage.root.is_absolute()
        assert storage.root.name == "storage"

    def test_root_property_returns_path(self, tmp_path):
        storage = StorageManager(tmp_path / "storage")
        assert storage.root == (tmp_path / "storage").resolve()

    def test_backend_property_returns_filesystem(self, tmp_path):
        storage = StorageManager(tmp_path / "storage")
        assert storage.backend == "filesystem"

    def test_backend_info_returns_metadata(self, tmp_path):
        storage = StorageManager(tmp_path / "storage")
        info = storage.backend_info()
        assert info["backend"] == "filesystem"
        assert info["root"] == str((tmp_path / "storage").resolve())


class TestPathResolution:
    """Tests for path resolution and validation."""

    def test_path_returns_validated_path(self, storage):
        path = storage.path("subdir", "file.txt")
        assert path == storage.root / "subdir" / "file.txt"

    def test_path_with_empty_parts(self, storage):
        path = storage.path("", "file.txt")
        assert path == storage.root / "file.txt"

    def test_path_traversal_outside_root_raises(self, storage, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        with pytest.raises(ValueError, match="Path traversal"):
            storage.path("../outside/file.txt")

    def test_path_traversal_with_absolute_path_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.path("/etc/passwd")

    def test_path_traversal_with_symlink_outside_root_raises(self, storage, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        link = storage.root / "link"
        link.symlink_to(outside)
        with pytest.raises(ValueError, match="Path traversal"):
            storage.path("link/file.txt")

    def test_path_with_multiple_traversal_attempts(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.path("../../etc/passwd")
        with pytest.raises(ValueError, match="Path traversal"):
            storage.path("subdir/../../etc/passwd")


class TestEnsureDirectory:
    """Tests for ensure_directory method."""

    def test_ensure_directory_creates_nested_directories(self, storage):
        path = storage.ensure_directory("a", "b", "c")
        assert path.exists()
        assert path.is_dir()
        assert path == storage.root / "a" / "b" / "c"

    def test_ensure_directory_existing_directory_returns_path(self, storage):
        storage.ensure_directory("existing")
        path = storage.ensure_directory("existing")
        assert path.exists()
        assert path.is_dir()

    def test_ensure_directory_with_empty_parts_returns_root(self, storage):
        path = storage.ensure_directory("")
        assert path == storage.root


class TestWriteText:
    """Tests for write_text method."""

    def test_write_text_creates_file_with_content(self, storage):
        path = storage.write_text("file.txt", "Hello, World!")
        assert path.exists()
        assert path.read_text() == "Hello, World!"

    def test_write_text_creates_parent_directories(self, storage):
        path = storage.write_text("deep/nested/file.txt", "content")
        assert path.exists()
        assert path.parent.exists()

    def test_write_text_overwrites_existing_file(self, storage):
        storage.write_text("file.txt", "original")
        path = storage.write_text("file.txt", "updated")
        assert path.read_text() == "updated"

    def test_write_text_with_unicode_content(self, storage):
        content = "Hello 🌍 你好 こんにちは"
        path = storage.write_text("unicode.txt", content)
        assert path.read_text() == content

    def test_write_text_with_empty_string(self, storage):
        path = storage.write_text("empty.txt", "")
        assert path.read_text() == ""

    def test_write_text_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.write_text("../outside.txt", "content")


class TestCreateFile:
    """Tests for create_file method."""

    def test_create_file_creates_empty_file(self, storage):
        path = storage.create_file("empty.txt")
        assert path.exists()
        assert path.is_file()
        assert path.stat().st_size == 0

    def test_create_file_creates_parent_directories(self, storage):
        path = storage.create_file("dir/subdir/file.txt")
        assert path.exists()
        assert path.parent.exists()

    def test_create_file_existing_file_returns_path(self, storage):
        storage.write_text("existing.txt", "content")
        path = storage.create_file("existing.txt")
        assert path.read_text() == "content"

    def test_create_file_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.create_file("../outside.txt")


class TestWriteJson:
    """Tests for write_json method."""

    def test_write_json_writes_valid_json(self, storage):
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        path = storage.write_json("data.json", data)
        assert path.exists()
        with path.open() as f:
            loaded = json.load(f)
        assert loaded == data

    def test_write_json_creates_parent_directories(self, storage):
        path = storage.write_json("nested/data.json", {"nested": True})
        assert path.exists()

    def test_write_json_overwrites_existing(self, storage):
        storage.write_json("data.json", {"original": True})
        storage.write_json("data.json", {"updated": True})
        assert storage.read_json("data.json") == {"updated": True}

    def test_write_json_with_complex_types(self, storage):
        data = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"a": "b"},
        }
        storage.write_json("complex.json", data)
        assert storage.read_json("complex.json") == data

    def test_write_json_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.write_json("../outside.json", {})


class TestReadText:
    """Tests for read_text method."""

    def test_read_text_returns_file_content(self, storage):
        storage.write_text("file.txt", "Hello, World!")
        content = storage.read_text("file.txt")
        assert content == "Hello, World!"

    def test_read_text_with_unicode_content(self, storage):
        content = "Hello 🌍 你好"
        storage.write_text("unicode.txt", content)
        assert storage.read_text("unicode.txt") == content

    def test_read_text_nonexistent_file_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read_text("nonexistent.txt")

    def test_read_text_directory_raises(self, storage):
        storage.ensure_directory("dir")
        with pytest.raises(IsADirectoryError):
            storage.read_text("dir")

    def test_read_text_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.read_text("../outside.txt")


class TestReadJson:
    """Tests for read_json method."""

    def test_read_json_returns_parsed_data(self, storage):
        storage.write_json("data.json", {"key": "value"})
        data = storage.read_json("data.json")
        assert data == {"key": "value"}

    def test_read_json_nonexistent_file_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read_json("nonexistent.json")

    def test_read_json_invalid_json_raises(self, storage):
        storage.write_text("invalid.json", "not json")
        with pytest.raises(json.JSONDecodeError):
            storage.read_json("invalid.json")

    def test_read_json_directory_raises(self, storage):
        storage.ensure_directory("dir")
        with pytest.raises(IsADirectoryError):
            storage.read_json("dir")

    def test_read_json_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.read_json("../outside.json")


class TestExists:
    """Tests for exists method."""

    def test_exists_returns_true_for_existing_file(self, storage):
        storage.write_text("file.txt", "content")
        assert storage.exists("file.txt") is True

    def test_exists_returns_true_for_existing_directory(self, storage):
        storage.ensure_directory("dir")
        assert storage.exists("dir") is True

    def test_exists_returns_false_for_nonexistent(self, storage):
        assert storage.exists("nonexistent") is False

    def test_exists_returns_false_for_nonexistent_nested(self, storage):
        assert storage.exists("dir/subdir/file.txt") is False

    def test_exists_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.exists("../outside")


class TestDelete:
    """Tests for delete method."""

    def test_delete_file_returns_true(self, storage):
        storage.write_text("file.txt", "content")
        assert storage.delete("file.txt") is True
        assert not storage.exists("file.txt")

    def test_delete_directory_returns_true(self, storage):
        storage.ensure_directory("dir")
        storage.write_text("dir/file.txt", "content")
        assert storage.delete("dir") is True
        assert not storage.exists("dir")

    def test_delete_nonexistent_returns_false(self, storage):
        assert storage.delete("nonexistent") is False

    def test_delete_nested_file(self, storage):
        storage.write_text("dir/subdir/file.txt", "content")
        assert storage.delete("dir/subdir/file.txt") is True
        assert not storage.exists("dir/subdir/file.txt")

    def test_delete_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.delete("../outside")


class TestCopy:
    """Tests for copy method."""

    def test_copy_file(self, storage):
        storage.write_text("source.txt", "content")
        dest = storage.copy("source.txt", "dest.txt")
        assert dest.exists()
        assert dest.read_text() == "content"
        assert storage.exists("source.txt")

    def test_copy_creates_destination_directory(self, storage):
        storage.write_text("source.txt", "content")
        dest = storage.copy("source.txt", "dir/dest.txt")
        assert dest.exists()
        assert dest.parent.exists()

    def test_copy_overwrites_existing(self, storage):
        storage.write_text("source.txt", "new content")
        storage.write_text("dest.txt", "old content")
        storage.copy("source.txt", "dest.txt")
        assert storage.read_text("dest.txt") == "new content"

    def test_copy_nonexistent_source_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.copy("nonexistent.txt", "dest.txt")

    def test_copy_directory_raises(self, storage):
        storage.ensure_directory("dir")
        with pytest.raises(IsADirectoryError):
            storage.copy("dir", "dest_dir")

    def test_copy_source_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.copy("../outside.txt", "dest.txt")

    def test_copy_dest_path_traversal_raises(self, storage):
        storage.write_text("source.txt", "content")
        with pytest.raises(ValueError, match="Path traversal"):
            storage.copy("source.txt", "../outside.txt")


class TestMove:
    """Tests for move method."""

    def test_move_file(self, storage):
        storage.write_text("source.txt", "content")
        dest = storage.move("source.txt", "dest.txt")
        assert dest.exists()
        assert dest.read_text() == "content"
        assert not storage.exists("source.txt")

    def test_move_creates_destination_directory(self, storage):
        storage.write_text("source.txt", "content")
        dest = storage.move("source.txt", "dir/dest.txt")
        assert dest.exists()
        assert dest.parent.exists()

    def test_move_overwrites_existing(self, storage):
        storage.write_text("source.txt", "new")
        storage.write_text("dest.txt", "old")
        storage.move("source.txt", "dest.txt")
        assert storage.read_text("dest.txt") == "new"
        assert not storage.exists("source.txt")

    def test_move_nonexistent_source_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.move("nonexistent.txt", "dest.txt")

    def test_move_source_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.move("../outside.txt", "dest.txt")

    def test_move_dest_path_traversal_raises(self, storage):
        storage.write_text("source.txt", "content")
        with pytest.raises(ValueError, match="Path traversal"):
            storage.move("source.txt", "../outside.txt")


class TestSize:
    """Tests for size method."""

    def test_size_returns_file_size_in_bytes(self, storage):
        content = "Hello, World!"
        storage.write_text("file.txt", content)
        assert storage.size("file.txt") == len(content.encode("utf-8"))

    def test_size_with_unicode_content(self, storage):
        content = "Hello 🌍"
        storage.write_text("file.txt", content)
        assert storage.size("file.txt") == len(content.encode("utf-8"))

    def test_size_empty_file_returns_zero(self, storage):
        storage.create_file("empty.txt")
        assert storage.size("empty.txt") == 0

    def test_size_nonexistent_file_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.size("nonexistent.txt")

    def test_size_directory_returns_size(self, storage):
        storage.ensure_directory("dir")
        # stat() on directory returns metadata size, not an error
        size = storage.size("dir")
        assert isinstance(size, int)
        assert size >= 0

    def test_size_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.size("../outside.txt")


class TestClear:
    """Tests for clear method."""

    def test_clear_removes_all_files_and_directories(self, storage):
        storage.write_text("file1.txt", "content1")
        storage.write_text("dir/file2.txt", "content2")
        storage.ensure_directory("empty_dir")
        storage.clear()
        assert storage.list() == []

    def test_clear_preserves_root_directory(self, storage):
        storage.write_text("file.txt", "content")
        storage.clear()
        assert storage.root.exists()
        assert storage.root.is_dir()

    def test_clear_on_empty_storage(self, storage):
        storage.clear()
        assert storage.list() == []


class TestHealthCheck:
    """Tests for health_check method."""

    def test_health_check_returns_true_for_accessible_storage(self, storage):
        assert storage.health_check() is True

    def test_health_check_returns_false_when_root_deleted(self, storage):
        import shutil
        shutil.rmtree(storage.root)
        assert storage.health_check() is False

    def test_health_check_returns_false_when_root_missing(self, storage):
        import shutil
        shutil.rmtree(storage.root)
        assert storage.health_check() is False


class TestList:
    """Tests for list method."""

    def test_list_returns_sorted_entries(self, storage):
        storage.write_text("c.txt", "c")
        storage.write_text("a.txt", "a")
        storage.ensure_directory("b_dir")
        entries = storage.list()
        assert [e.name for e in entries] == ["a.txt", "b_dir", "c.txt"]

    def test_list_subdirectory(self, storage):
        storage.write_text("dir/a.txt", "a")
        storage.write_text("dir/b.txt", "b")
        entries = storage.list("dir")
        assert [e.name for e in entries] == ["a.txt", "b.txt"]

    def test_list_nonexistent_directory_returns_empty(self, storage):
        entries = storage.list("nonexistent")
        assert entries == []

    def test_list_empty_directory_returns_empty(self, storage):
        storage.ensure_directory("empty")
        assert storage.list("empty") == []

    def test_list_file_raises_not_directory(self, storage):
        storage.write_text("file.txt", "content")
        with pytest.raises(NotADirectoryError):
            storage.list("file.txt")

    def test_list_path_traversal_raises(self, storage):
        with pytest.raises(ValueError, match="Path traversal"):
            storage.list("../outside")


class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_path_with_special_characters(self, storage):
        path = storage.path("file with spaces.txt")
        assert path.name == "file with spaces.txt"

    def test_path_with_unicode_characters(self, storage):
        path = storage.path("文件.txt")
        assert path.name == "文件.txt"

    def test_nested_path_operations(self, storage):
        storage.ensure_directory("a", "b", "c")
        storage.write_text("a/b/c/file.txt", "content")
        assert storage.read_text("a/b/c/file.txt") == "content"
        storage.move("a/b/c/file.txt", "a/moved.txt")
        assert storage.read_text("a/moved.txt") == "content"

    def test_operations_on_hidden_files(self, storage):
        storage.write_text(".hidden", "secret")
        assert storage.exists(".hidden")
        assert storage.read_text(".hidden") == "secret"
        storage.delete(".hidden")
        assert not storage.exists(".hidden")

    def test_operations_with_long_paths(self, storage):
        deep_path = "/".join(["dir"] * 50 + ["file.txt"])
        storage.write_text(deep_path, "deep")
        assert storage.read_text(deep_path) == "deep"

    def test_clear_removes_hidden_files(self, storage):
        storage.write_text(".hidden", "hidden")
        storage.write_text("visible.txt", "visible")
        storage.clear()
        assert storage.list() == []

    def test_write_and_read_large_content(self, storage):
        large_content = "x" * 100_000
        storage.write_text("large.txt", large_content)
        assert storage.read_text("large.txt") == large_content

    def test_move_file_into_existing_directory(self, storage):
        storage.ensure_directory("dir")
        storage.write_text("file.txt", "content")
        dest = storage.move("file.txt", "dir")
        # shutil.move returns the destination directory when moving into a directory
        moved_file = storage.root / "dir" / "file.txt"
        assert moved_file.exists()
        assert moved_file.read_text() == "content"
        assert not storage.exists("file.txt")

    def test_copy_file_into_existing_directory(self, storage):
        storage.ensure_directory("dir")
        storage.write_text("file.txt", "content")
        dest = storage.copy("file.txt", "dir")
        copied_file = storage.root / "dir" / "file.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "content"
        assert storage.exists("file.txt")

    def test_root_path_is_absolute_and_resolved(self, tmp_path):
        storage = StorageManager(tmp_path / "storage")
        assert storage.root.is_absolute()
        assert storage.root == (tmp_path / "storage").resolve()


class TestStateTransitions:
    """Tests for state transitions and resource cleanup."""

    def test_multiple_operations_maintain_consistency(self, storage):
        storage.write_text("a.txt", "a")
        storage.write_text("b.txt", "b")
        storage.move("a.txt", "c.txt")
        storage.delete("b.txt")
        storage.write_text("d.txt", "d")
        assert storage.list() == [storage.root / "c.txt", storage.root / "d.txt"]

    def test_clear_then_write_works(self, storage):
        storage.write_text("file.txt", "content")
        storage.clear()
        storage.write_text("new.txt", "new content")
        assert storage.read_text("new.txt") == "new content"

    def test_health_check_after_clear(self, storage):
        storage.write_text("file.txt", "content")
        storage.clear()
        assert storage.health_check() is True

    def test_health_check_after_operations(self, storage):
        storage.write_text("file.txt", "content")
        storage.ensure_directory("dir")
        storage.move("file.txt", "dir/file.txt")
        storage.copy("dir/file.txt", "copy.txt")
        storage.delete("copy.txt")
        assert storage.health_check() is True


class TestInvalidInputs:
    """Tests for invalid input handling."""

    def test_path_with_none_raises(self, storage):
        with pytest.raises((TypeError, AttributeError)):
            storage.path(None)

    def test_write_text_with_none_content_raises(self, storage):
        with pytest.raises(TypeError):
            storage.write_text("file.txt", None)

    def test_write_json_with_non_serializable_raises(self, storage):
        import datetime
        with pytest.raises(TypeError):
            storage.write_json("file.json", {"date": datetime.datetime.now()})

    def test_write_json_with_non_serializable_raises(self, storage):
        import datetime
        with pytest.raises(TypeError):
            storage.write_json("file.json", {"date": datetime.datetime.now()})

    def test_copy_with_none_args_raises(self, storage):
        with pytest.raises(TypeError):
            storage.copy(None, "dest.txt")
        with pytest.raises(TypeError):
            storage.copy("source.txt", None)

    def test_move_with_none_args_raises(self, storage):
        with pytest.raises(TypeError):
            storage.move(None, "dest.txt")
        with pytest.raises(TypeError):
            storage.move("source.txt", None)

    def test_exists_with_none_raises(self, storage):
        with pytest.raises((TypeError, AttributeError)):
            storage.exists(None)

    def test_delete_with_none_raises(self, storage):
        with pytest.raises((TypeError, AttributeError)):
            storage.delete(None)


class TestConcurrentOperations:
    """Tests for concurrent-like operations (sequential simulation)."""

    def test_multiple_writes_and_reads(self, storage):
        for i in range(100):
            storage.write_text(f"file_{i}.txt", f"content {i}")
        for i in range(100):
            assert storage.read_text(f"file_{i}.txt") == f"content {i}"

    def test_many_nested_directories(self, storage):
        path = storage.ensure_directory(*[f"dir_{i}" for i in range(20)])
        assert path.exists()
        assert len(path.parts) - len(storage.root.parts) == 20

    def test_mixed_operations(self, storage):
        for i in range(10):
            storage.write_text(f"file_{i}.txt", str(i))
            if i % 2 == 0:
                storage.ensure_directory(f"dir_{i}")
        storage.delete("file_0.txt")
        storage.move("file_1.txt", "moved_1.txt")
        storage.copy("file_2.txt", "copy_2.txt")
        assert storage.exists("moved_1.txt")
        assert storage.exists("copy_2.txt")
        assert not storage.exists("file_0.txt")


class TestStorageManagerBackend:
    """Tests for backend property and info."""

    def test_default_backend_is_filesystem(self, storage):
        assert storage.backend == "filesystem"
        assert storage.backend_info()["backend"] == "filesystem"

    def test_backend_info_includes_root_path(self, tmp_path):
        storage = StorageManager(tmp_path / "custom_storage")
        info = storage.backend_info()
        assert info["root"] == str((tmp_path / "custom_storage").resolve())


# Fixtures
@pytest.fixture
def storage(tmp_path):
    """Provide a StorageManager instance with a temporary directory."""
    return StorageManager(tmp_path / "storage")