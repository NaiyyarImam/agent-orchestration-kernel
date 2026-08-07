"""Unit tests for OllamaProvider."""

from __future__ import annotations

import json

import httpx
import pytest

from kernel.models.ollama_provider import OllamaProvider


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    """Replace httpx.AsyncClient with a MockTransport-backed client."""
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        kwargs["transport"] = transport
        return real_client(**kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def _patch_sync_client(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    """Replace httpx.Client with a MockTransport-backed client."""
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def factory(**kwargs):
        kwargs["transport"] = transport
        return real_client(**kwargs)

    monkeypatch.setattr(httpx, "Client", factory)


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

    @pytest.mark.asyncio
    async def test_model_info_returns_metadata() -> None:
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.model_info() == provider.metadata


class TestNativeBaseUrl:
    """Tests for native API base URL derivation."""

    def test_strips_v1_suffix(self) -> None:
        provider = OllamaProvider(model="qwen3:14b", base_url="http://host:11434/v1")
        assert provider._native_base_url() == "http://host:11434"

    def test_keeps_url_without_suffix(self) -> None:
        provider = OllamaProvider(model="qwen3:14b", base_url="http://host:11434")
        assert provider._native_base_url() == "http://host:11434"

    def test_keeps_url_with_trailing_slash(self) -> None:
        provider = OllamaProvider(model="qwen3:14b", base_url="http://host:11434/v1/")
        assert provider._native_base_url() == "http://host:11434"


class TestGenerate:
    """Tests for the generate method."""

    @pytest.mark.asyncio
    async def test_generate_success_with_system_prompt(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["payload"] = request.read().decode()
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Hello from Ollama"}}]},
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.generate(
            "Say hello",
            system_prompt="Be concise",
            max_tokens=50,
            temperature=0.5,
            extra_field="value",
        )

        assert result == "Hello from Ollama"
        assert captured["url"].endswith("/chat/completions")
        payload = json.loads(captured["payload"])
        assert payload["model"] == "qwen3:14b"
        assert payload["messages"] == [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "Say hello"},
        ]
        assert payload["max_tokens"] == 50
        assert payload["temperature"] == 0.5
        assert payload["extra_field"] == "value"

    @pytest.mark.asyncio
    async def test_generate_without_system_prompt_or_max_tokens(
        self, monkeypatch
    ) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["payload"] = request.read().decode()
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.generate("Hello")

        assert result == "ok"
        payload = json.loads(captured["payload"])
        assert payload["messages"] == [{"role": "user", "content": "Hello"}]
        assert "max_tokens" not in payload

    @pytest.mark.asyncio
    async def test_generate_http_error_raises(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="server error")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(httpx.HTTPStatusError):
            await provider.generate("Hello")

    @pytest.mark.asyncio
    async def test_generate_network_error_raises(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(httpx.ConnectError):
            await provider.generate("Hello")

    @pytest.mark.asyncio
    async def test_generate_invalid_response_raises_key_error(
        self, monkeypatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"unexpected": "shape"})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(KeyError):
            await provider.generate("Hello")

    @pytest.mark.asyncio
    async def test_generate_missing_content_raises_key_error(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"choices": [{}]})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(KeyError):
            await provider.generate("Hello")


class TestEmbed:
    """Tests for the embed method."""

    @pytest.mark.asyncio
    async def test_embed_openai_style_response(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["payload"] = request.read().decode()
            return httpx.Response(
                200,
                json={"data": [{"embedding": [0.1, 0.2, 0.3]}]},
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.embed("hello world")

        assert result == [0.1, 0.2, 0.3]
        assert captured["url"].endswith("/embeddings")
        payload = json.loads(captured["payload"])
        assert payload["model"] == "qwen3:14b"
        assert payload["input"] == "hello world"

    @pytest.mark.asyncio
    async def test_embed_legacy_response(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embedding": [1.0, 2.0]})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.embed("text")

        assert result == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_embed_empty_data_list_falls_back(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": []})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.embed("text")

        assert result == []

    @pytest.mark.asyncio
    async def test_embed_missing_embedding_defaults_to_empty(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": [{"other": "field"}]})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.embed("text")

        assert result == []

    @pytest.mark.asyncio
    async def test_embed_http_error_raises(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="unavailable")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(httpx.HTTPStatusError):
            await provider.embed("text")


class TestHealthCheck:
    """Tests for the health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(
                200,
                json={"models": [{"name": "qwen3:14b"}]},
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.health_check() is True
        assert captured["url"].endswith("/api/tags")
        assert "/v1" not in captured["url"]

    @pytest.mark.asyncio
    async def test_health_check_missing_models_list_is_unhealthy(
        self, monkeypatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": None})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_non_dict_json_is_unhealthy(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[1, 2, 3])

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_http_error_returns_false(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="error")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_network_error_returns_false(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("timed out")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.health_check() is False

    @pytest.mark.asyncio
    async def test_health_check_uses_base_url_without_v1(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(200, json={"models": []})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b", base_url="http://custom:11434/v1")

        await provider.health_check()

        assert captured["url"] == "http://custom:11434/api/tags"


class TestPing:
    """Tests for the ping method."""

    @pytest.mark.asyncio
    async def test_ping_delegates_to_health_check(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.ping() is True


class TestAvailableModels:
    """Tests for model discovery."""

    @pytest.mark.asyncio
    async def test_available_models_returns_names(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "qwen3:14b"},
                        {"name": "mistral:latest"},
                    ]
                },
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = await provider.available_models()

        assert result == ["qwen3:14b", "mistral:latest"]
        assert captured["url"].endswith("/api/tags")

    @pytest.mark.asyncio
    async def test_available_models_filters_entries_without_name(
        self, monkeypatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "qwen3:14b"},
                        {"size": 123},
                        {"name": "mistral:latest"},
                    ]
                },
            )

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.available_models() == ["qwen3:14b", "mistral:latest"]

    @pytest.mark.asyncio
    async def test_available_models_missing_models_key(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"other": "data"})

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert await provider.available_models() == []

    @pytest.mark.asyncio
    async def test_available_models_http_error_raises(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="error")

        _patch_async_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(httpx.HTTPStatusError):
            await provider.available_models()


class TestAvailableModelsSync:
    """Tests for synchronous model discovery."""

    def test_available_models_sync_returns_names(self, monkeypatch) -> None:
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "qwen3:14b"},
                        {"name": "mistral:latest"},
                    ]
                },
            )

        _patch_sync_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        result = provider.available_models_sync()

        assert result == ["qwen3:14b", "mistral:latest"]
        assert captured["url"].endswith("/api/tags")

    def test_available_models_sync_filters_entries_without_name(
        self, monkeypatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"models": [{"name": "qwen3:14b"}, {"size": 1}]},
            )

        _patch_sync_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        assert provider.available_models_sync() == ["qwen3:14b"]

    def test_available_models_sync_http_error_raises(self, monkeypatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="error")

        _patch_sync_client(monkeypatch, handler)
        provider = OllamaProvider(model="qwen3:14b")

        with pytest.raises(httpx.HTTPStatusError):
            provider.available_models_sync()
