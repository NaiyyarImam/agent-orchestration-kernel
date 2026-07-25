

"""Unit tests for ConfigManager."""

from __future__ import annotations

from pathlib import Path

from kernel.config.config_manager import ConfigManager


def test_config_manager_initializes(config_manager: ConfigManager) -> None:
    """ConfigManager can be constructed."""
    assert isinstance(config_manager, ConfigManager)


def test_storage_configuration(config_manager: ConfigManager) -> None:
    """Storage configuration exposes expected paths."""
    assert isinstance(config_manager.storage.root, Path)
    assert isinstance(config_manager.storage.database, Path)
    assert config_manager.storage.database.name.endswith(".db")


def test_ollama_configuration(config_manager: ConfigManager) -> None:
    """Ollama configuration contains required values."""
    assert config_manager.ollama.base_url.startswith("http")
    assert config_manager.ollama.default_model


def test_project_root_exists(config_manager: ConfigManager) -> None:
    """Project root should exist on disk."""
    assert config_manager.project_root.exists()
    assert config_manager.project_root.is_dir()