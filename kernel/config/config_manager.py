

"""Central configuration manager for the JARVIS Kernel.

Every Kernel component must obtain configuration through this manager rather
than reading environment variables directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(slots=True, frozen=True)
class KernelConfig:
    """Immutable Kernel configuration."""

    project_root: Path
    workspace_path: Path
    storage_path: Path
    ollama_base_url: str
    default_model: str
    log_level: str
    debug: bool


class ConfigManager:
    """Loads and exposes Kernel configuration."""

    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parents[2]

        self._config = KernelConfig(
            project_root=project_root,
            workspace_path=Path(
                os.getenv("JARVIS_WORKSPACE", str(project_root / "project"))
            ),
            storage_path=Path(
                os.getenv("JARVIS_STORAGE", str(project_root / "storage"))
            ),
            ollama_base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://127.0.0.1:11434",
            ),
            default_model=os.getenv(
                "JARVIS_DEFAULT_MODEL",
                "qwen3:14b",
            ),
            log_level=os.getenv("JARVIS_LOG_LEVEL", "INFO"),
            debug=os.getenv("JARVIS_DEBUG", "false").lower() == "true",
        )

    @property
    def config(self) -> KernelConfig:
        """Return the immutable configuration object."""
        return self._config

    def get(self, key: str):
        """Retrieve a configuration value by attribute name."""
        if not hasattr(self._config, key):
            raise KeyError(f"Unknown configuration key: {key}")
        return getattr(self._config, key)

    def as_dict(self) -> dict[str, object]:
        """Return the configuration as a dictionary."""
        return {
            field: getattr(self._config, field)
            for field in self._config.__dataclass_fields__
        }