"""Unit tests for ModelManager."""

from __future__ import annotations

from typing import Any

import pytest

from kernel.interfaces.model_provider import ModelProvider
from kernel.models.model_manager import ModelManager


class FakeProvider(ModelProvider):
    """Deterministic ModelProvider used for manager testing."""

    def __init__(
        self,
        name: str,
        *,
        healthy: bool = True,
    ) -> None:
        self._name = name
        self._healthy = healthy
        self.generate_calls: list[dict[str, Any]] = []
        self.embed_calls: list[dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "provider": "fake",
            "model": self._name,
            "base_url": "http://fake",
            "timeout": 1.0,
        }

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        self.generate_calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "kwargs": kwargs,
            }
        )
        return f"generated-{self._name}"

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        self.embed_calls.append({"text": text, "kwargs": kwargs})
        return [0.1, 0.2]

    async def health_check(self) -> bool:
        return self._healthy


@pytest.fixture
def manager() -> ModelManager:
    """Provide an empty ModelManager."""
    return ModelManager()


@pytest.fixture
def populated_manager(manager: ModelManager) -> ModelManager:
    """Provide a manager with two registered providers."""
    manager.register(FakeProvider("alpha"))
    manager.register(FakeProvider("beta"))
    return manager


class TestRegister:
    """Tests for provider registration."""

    def test_register_model(self) -> None:
        manager = ModelManager()
        provider = FakeProvider("qwen3:14b")

        manager.register(provider)

        assert manager.get("qwen3:14b") is provider

    def test_register_sets_default_for_first_provider(self) -> None:
        manager = ModelManager()

        manager.register(FakeProvider("alpha"))

        assert manager.default_provider_name() == "alpha"

    def test_register_default_flag_overrides_existing_default(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        provider = FakeProvider("beta")

        manager.register(provider, default=True)

        assert manager.default() is provider

    def test_register_without_default_keeps_existing_default(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        provider = FakeProvider("beta")

        manager.register(provider)

        assert manager.default_provider_name() == "alpha"

    def test_register_replaces_existing_provider(self) -> None:
        manager = ModelManager()
        replacement = FakeProvider("alpha")

        manager.register(FakeProvider("alpha"))
        manager.register(replacement)

        assert manager.get("alpha") is replacement
        assert manager.provider_count() == 1


class TestUnregister:
    """Tests for provider unregistration."""

    def test_unregister_existing_provider(self, populated_manager: ModelManager) -> None:
        assert populated_manager.unregister("alpha") is True
        assert populated_manager.has_provider("alpha") is False
        assert populated_manager.provider_count() == 1

    def test_unregister_unknown_provider_returns_false(self, manager: ModelManager) -> None:
        assert manager.unregister("does-not-exist") is False

    def test_unregister_default_provider_selects_another(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("beta"))

        manager.unregister("alpha")

        assert manager.default_provider_name() == "beta"

    def test_unregister_default_provider_from_single_provider(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))

        manager.unregister("alpha")

        assert manager.default_provider_name() is None
        assert manager.provider_count() == 0


class TestGet:
    """Tests for provider lookup."""

    def test_get_registered_provider(self, populated_manager: ModelManager) -> None:
        provider = populated_manager.get("alpha")
        assert provider.name == "alpha"

    def test_get_missing_provider_raises_key_error(self, manager: ModelManager) -> None:
        with pytest.raises(KeyError, match="Unknown model provider"):
            manager.get("does-not-exist")


class TestDefault:
    """Tests for default provider access."""

    def test_default_returns_default_provider(self, populated_manager: ModelManager) -> None:
        assert populated_manager.default().name == "alpha"

    def test_default_raises_when_no_provider_exists(self, manager: ModelManager) -> None:
        with pytest.raises(RuntimeError, match="No default model provider"):
            manager.default()


class TestProviders:
    """Tests for provider enumeration."""

    def test_providers_returns_sorted_names(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("zeta"))
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("middle"))

        assert manager.providers() == ["alpha", "middle", "zeta"]

    def test_providers_empty(self, manager: ModelManager) -> None:
        assert manager.providers() == []


class TestHasProvider:
    """Tests for provider existence checks."""

    def test_has_provider_registered(self, populated_manager: ModelManager) -> None:
        assert populated_manager.has_provider("alpha") is True

    def test_has_provider_missing(self, manager: ModelManager) -> None:
        assert manager.has_provider("alpha") is False


class TestProviderCount:
    """Tests for provider counting."""

    def test_provider_count_empty(self, manager: ModelManager) -> None:
        assert manager.provider_count() == 0

    def test_provider_count_after_registration(self, populated_manager: ModelManager) -> None:
        assert populated_manager.provider_count() == 2

    def test_provider_count_after_unregister(self, populated_manager: ModelManager) -> None:
        populated_manager.unregister("alpha")
        assert populated_manager.provider_count() == 1


class TestActiveProvider:
    """Tests for the active provider alias."""

    def test_active_provider_returns_default(self, populated_manager: ModelManager) -> None:
        assert populated_manager.active_provider() is populated_manager.default()

    def test_active_provider_raises_when_empty(self, manager: ModelManager) -> None:
        with pytest.raises(RuntimeError):
            manager.active_provider()


class TestDefaultProviderName:
    """Tests for the default provider name accessor."""

    def test_default_provider_name_registered(self, populated_manager: ModelManager) -> None:
        assert populated_manager.default_provider_name() == "alpha"

    def test_default_provider_name_none_when_empty(self, manager: ModelManager) -> None:
        assert manager.default_provider_name() is None

    def test_default_provider_name_reflects_set_default(
        self, populated_manager: ModelManager
    ) -> None:
        populated_manager.set_default("beta")
        assert populated_manager.default_provider_name() == "beta"


class TestProviderInfo:
    """Tests for the provider info snapshot."""

    def test_provider_info_empty(self, manager: ModelManager) -> None:
        info = manager.provider_info()
        assert info == {
            "default_provider": None,
            "providers": [],
            "provider_count": 0,
        }

    def test_provider_info_populated(self, populated_manager: ModelManager) -> None:
        info = populated_manager.provider_info()
        assert info["default_provider"] == "alpha"
        assert info["providers"] == ["alpha", "beta"]
        assert info["provider_count"] == 2


class TestSetDefault:
    """Tests for explicit default selection."""

    def test_set_default_success(self, populated_manager: ModelManager) -> None:
        populated_manager.set_default("beta")
        assert populated_manager.default().name == "beta"

    def test_set_default_unknown_provider_raises_key_error(
        self, populated_manager: ModelManager
    ) -> None:
        with pytest.raises(KeyError, match="Unknown model provider"):
            populated_manager.set_default("does-not-exist")


class TestGenerate:
    """Tests for text generation delegation."""

    @pytest.mark.asyncio
    async def test_generate_delegates_to_default(self, populated_manager: ModelManager) -> None:
        result = await populated_manager.generate("hello")

        assert result == "generated-alpha"
        provider = populated_manager.get("alpha")
        assert len(provider.generate_calls) == 1
        assert provider.generate_calls[0]["prompt"] == "hello"

    @pytest.mark.asyncio
    async def test_generate_delegates_to_explicit_provider(
        self, populated_manager: ModelManager
    ) -> None:
        result = await populated_manager.generate("hello", provider="beta")

        assert result == "generated-beta"
        assert populated_manager.get("beta").generate_calls == [
            {
                "prompt": "hello",
                "system_prompt": None,
                "temperature": 0.2,
                "max_tokens": None,
                "kwargs": {},
            }
        ]
        assert populated_manager.get("alpha").generate_calls == []

    @pytest.mark.asyncio
    async def test_generate_forwards_all_arguments(
        self, populated_manager: ModelManager
    ) -> None:
        await populated_manager.generate(
            "prompt text",
            system_prompt="system text",
            temperature=0.8,
            max_tokens=100,
            stop=["\n"],
            seed=42,
        )

        assert populated_manager.get("alpha").generate_calls == [
            {
                "prompt": "prompt text",
                "system_prompt": "system text",
                "temperature": 0.8,
                "max_tokens": 100,
                "kwargs": {"stop": ["\n"], "seed": 42},
            }
        ]

    @pytest.mark.asyncio
    async def test_generate_unknown_provider_raises_key_error(
        self, populated_manager: ModelManager
    ) -> None:
        with pytest.raises(KeyError, match="Unknown model provider"):
            await populated_manager.generate("hello", provider="does-not-exist")

    @pytest.mark.asyncio
    async def test_generate_empty_manager_raises_runtime_error(
        self, manager: ModelManager
    ) -> None:
        with pytest.raises(RuntimeError):
            await manager.generate("hello")


class TestEmbed:
    """Tests for embedding delegation."""

    @pytest.mark.asyncio
    async def test_embed_delegates_to_default(self, populated_manager: ModelManager) -> None:
        result = await populated_manager.embed("text")

        assert result == [0.1, 0.2]
        provider = populated_manager.get("alpha")
        assert len(provider.embed_calls) == 1
        assert provider.embed_calls[0]["text"] == "text"
        assert provider.embed_calls[0]["kwargs"] == {}

    @pytest.mark.asyncio
    async def test_embed_delegates_to_explicit_provider(
        self, populated_manager: ModelManager
    ) -> None:
        await populated_manager.embed("text", provider="beta")

        assert populated_manager.get("beta").embed_calls == [
            {"text": "text", "kwargs": {}}
        ]
        assert populated_manager.get("alpha").embed_calls == []

    @pytest.mark.asyncio
    async def test_embed_forwards_kwargs(self, populated_manager: ModelManager) -> None:
        await populated_manager.embed("text", provider="beta", truncate=True)

        assert populated_manager.get("beta").embed_calls == [
            {"text": "text", "kwargs": {"truncate": True}}
        ]

    @pytest.mark.asyncio
    async def test_embed_unknown_provider_raises_key_error(
        self, populated_manager: ModelManager
    ) -> None:
        with pytest.raises(KeyError, match="Unknown model provider"):
            await populated_manager.embed("text", provider="does-not-exist")

    @pytest.mark.asyncio
    async def test_embed_empty_manager_raises_runtime_error(
        self, manager: ModelManager
    ) -> None:
        with pytest.raises(RuntimeError):
            await manager.embed("text")


class TestSelectDefault:
    """Tests for the select_default method."""

    def test_select_default_no_providers_raises(self, manager: ModelManager) -> None:
        with pytest.raises(RuntimeError, match="No model providers are registered"):
            manager.select_default("qwen3:14b")

    def test_select_default_preferred_exists(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("qwen3:14b"))

        selected = manager.select_default("qwen3:14b")

        assert selected == "qwen3:14b"
        assert manager.default_provider_name() == "qwen3:14b"

    def test_select_default_preferred_missing_falls_back_to_first(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("beta"))

        selected = manager.select_default("does-not-exist")

        assert selected == "alpha"
        assert manager.default_provider_name() == "alpha"

    def test_select_default_preferred_missing_keeps_valid_default(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("beta"))
        manager.set_default("beta")

        selected = manager.select_default("does-not-exist")

        assert selected == "beta"

    def test_select_default_preferred_missing_after_default_removed(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("alpha"))
        manager.register(FakeProvider("beta"))
        manager.set_default("beta")
        manager.unregister("beta")

        selected = manager.select_default("does-not-exist")

        assert selected == "alpha"


class TestSupportsProvider:
    """Tests for provider support checks."""

    def test_supports_provider_registered(self, populated_manager: ModelManager) -> None:
        assert populated_manager.supports_provider("alpha") is True

    def test_supports_provider_missing(self, manager: ModelManager) -> None:
        assert manager.supports_provider("alpha") is False


class TestHealthCheck:
    """Tests for aggregate health checking."""

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, populated_manager: ModelManager) -> None:
        result = await populated_manager.health_check()

        assert result == {"alpha": True, "beta": True}

    @pytest.mark.asyncio
    async def test_health_check_mixed_statuses(self) -> None:
        manager = ModelManager()
        manager.register(FakeProvider("healthy", healthy=True))
        manager.register(FakeProvider("unhealthy", healthy=False))

        result = await manager.health_check()

        assert result == {"healthy": True, "unhealthy": False}

    @pytest.mark.asyncio
    async def test_health_check_empty_registry(self, manager: ModelManager) -> None:
        assert await manager.health_check() == {}

    @pytest.mark.asyncio
    async def test_health_check_after_unregister(self, populated_manager: ModelManager) -> None:
        populated_manager.unregister("alpha")

        assert await populated_manager.health_check() == {"beta": True}
