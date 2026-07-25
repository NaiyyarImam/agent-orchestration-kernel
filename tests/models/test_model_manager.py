

"""Unit tests for ModelManager."""

from __future__ import annotations

from kernel.models.model_manager import ModelManager
from kernel.models.ollama_provider import OllamaProvider
import pytest


def test_register_model() -> None:
    manager = ModelManager()
    provider = OllamaProvider(model="qwen3:14b")

    manager.register(provider)

    assert manager.get("qwen3:14b") is provider


def test_list_models() -> None:
    manager = ModelManager()

    manager.register(OllamaProvider(model="qwen3:14b"))
    manager.register(OllamaProvider(model="mistral:latest"))

    assert manager.get("qwen3:14b").name == "qwen3:14b"
    assert manager.get("mistral:latest").name == "mistral:latest"


def test_default_model_selection() -> None:
    manager = ModelManager()
    provider = OllamaProvider(model="qwen3:14b")

    manager.register(provider)
    manager.set_default("qwen3:14b")

    assert manager.default() is provider


def test_missing_model_returns_none() -> None:
    manager = ModelManager()

    with pytest.raises(KeyError):
        manager.get("does-not-exist")