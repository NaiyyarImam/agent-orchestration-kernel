

"""Storage manager for the JARVIS Kernel.

Provides a backend-agnostic abstraction for filesystem storage. Future
implementations can extend this to support SQLite, vector databases,
and remote storage without changing Kernel components.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final
import json
import os
import shutil


class StorageManager:
    """Manage Kernel storage locations and filesystem operations."""

    DEFAULT_BACKEND: Final[str] = "filesystem"

    def __init__(self, root: Path) -> None:
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._backend = self.DEFAULT_BACKEND

    @property
    def root(self) -> Path:
        """Return the root storage directory."""
        return self._root

    @property
    def backend(self) -> str:
        """Return the active storage backend name."""
        return self._backend

    def _resolve(self, relative_path: str) -> Path:
        """Resolve and validate a path beneath the storage root."""
        target = (self._root / relative_path).resolve()

        if os.path.commonpath([str(self._root), str(target)]) != str(self._root):
            raise ValueError("Path traversal outside storage root is not allowed.")

        return target

    def path(self, *parts: str) -> Path:
        """Return a validated path beneath the storage root."""
        return self._resolve(str(Path(*parts)))

    def ensure_directory(self, *parts: str) -> Path:
        """Create a directory if it does not already exist."""
        directory = self.path(*parts)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_text(self, relative_path: str, content: str) -> Path:
        """Write UTF-8 text to a file beneath the storage root."""
        destination = self.path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination

    def create_file(self, relative_path: str) -> Path:
        """Create an empty file if it does not exist."""
        file_path = self.path(relative_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)
        return file_path

    def write_json(self, relative_path: str, data: dict) -> Path:
        """Write JSON data."""
        destination = self.path(relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        return destination

    def read_text(self, relative_path: str) -> str:
        """Read UTF-8 text from a file beneath the storage root."""
        return self.path(relative_path).read_text(encoding="utf-8")

    def read_json(self, relative_path: str) -> dict:
        """Read JSON data."""
        with self.path(relative_path).open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def exists(self, relative_path: str) -> bool:
        """Return True if a file or directory exists."""
        return self.path(relative_path).exists()

    def delete(self, relative_path: str) -> bool:
        """Delete a file or directory. Return True if removed."""
        target = self.path(relative_path)
        if not target.exists():
            return False
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return True

    def copy(self, source: str, destination: str) -> Path:
        """Copy a file."""
        src = self.path(source)
        dst = self.path(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return dst

    def move(self, source: str, destination: str) -> Path:
        """Move a file."""
        src = self.path(source)
        dst = self.path(destination)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        return dst

    def size(self, relative_path: str) -> int:
        """Return file size in bytes."""
        return self.path(relative_path).stat().st_size

    def clear(self) -> None:
        """Remove everything beneath the storage root."""
        for item in self._root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def health_check(self) -> bool:
        """Verify the storage directory is accessible."""
        return self._root.exists() and self._root.is_dir()

    def list(self, relative_path: str = "") -> list[Path]:
        """List entries beneath a directory."""
        directory = self.path(relative_path)
        if not directory.exists():
            return []
        return sorted(directory.iterdir())

    def backend_info(self) -> dict[str, str]:
        """Return metadata describing the active storage backend."""
        return {
            "backend": self._backend,
            "root": str(self._root),
        }