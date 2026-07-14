
"""Unit tests for OllamaProvider."""

from __future__ import annotations

from kernel.models.ollama_provider import OllamaProvider


def test_provider_name() -> None:
    provider = OllamaProvider(model="qwen3:14b")
    assert provider.name == "qwen3:14b"


def test_provider_metadata() -> None:
    provider = OllamaProvider(model="qwen3:14b")

    metadata = provider.metadata

    assert metadata["provider"] == "ollama"
    assert metadata["model"] == "qwen3:14b"
    assert metadata["base_url"].startswith("http")
    assert metadata["timeout"] > 0


def test_base_url_property() -> None:
    provider = OllamaProvider(model="mistral:latest")

    assert provider.base_url.startswith("http")


def test_timeout_property() -> None:
    provider = OllamaProvider(model="mistral:latest", timeout=60.0)

    assert provider.timeout == 60.0