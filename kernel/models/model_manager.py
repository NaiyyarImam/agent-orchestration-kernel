"""Model manager for the JARVIS Kernel.

The ModelManager owns the lifecycle of all language model providers.
Kernel components must obtain model access through this manager rather
than communicating with providers directly.
"""

from __future__ import annotations

from typing import Any

from kernel.interfaces.model_provider import ModelProvider


class ModelManager:
    """Central registry for ModelProvider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {}
        self._default_provider: str | None = None

    def register(
        self,
        provider: ModelProvider,
        *,
        default: bool = False,
    ) -> None:
        """Register a model provider."""

        self._providers[provider.name] = provider

        if default or self._default_provider is None:
            self._default_provider = provider.name

    def unregister(self, provider_name: str) -> bool:
        """Remove a registered provider."""

        if provider_name not in self._providers:
            return False

        del self._providers[provider_name]

        if self._default_provider == provider_name:
            self._default_provider = (
                next(iter(self._providers), None)
            )

        return True

    def get(self, provider_name: str) -> ModelProvider:
        """Return a registered provider."""

        try:
            return self._providers[provider_name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown model provider: {provider_name}"
            ) from exc

    def default(self) -> ModelProvider:
        """Return the default provider."""

        if self._default_provider is None:
            raise RuntimeError("No default model provider configured.")

        return self.get(self._default_provider)

    def providers(self) -> list[str]:
        """Return registered provider names."""

        return sorted(self._providers.keys())

    def has_provider(self, provider_name: str) -> bool:
        """Return True if a provider is registered."""
        return provider_name in self._providers

    def provider_count(self) -> int:
        """Return the number of registered providers."""
        return len(self._providers)

    def active_provider(self) -> ModelProvider:
        """Return the currently selected default provider."""
        return self.default()

    def default_provider_name(self) -> str | None:
        """Return the default provider name."""
        return self._default_provider

    def provider_info(self) -> dict[str, Any]:
        """Return metadata describing the model manager state."""
        return {
            "default_provider": self._default_provider,
            "providers": self.providers(),
            "provider_count": self.provider_count(),
        }

    def set_default(self, provider_name: str) -> None:
        """Set the default provider."""

        if provider_name not in self._providers:
            raise KeyError(
                f"Unknown model provider: {provider_name}"
            )

        self._default_provider = provider_name

    async def generate(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using the selected provider."""

        model = (
            self.default()
            if provider is None
            else self.get(provider)
        )

        return await model.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def embed(
        self,
        text: str,
        *,
        provider: str | None = None,
        **kwargs: Any,
    ) -> list[float]:
        """Generate embeddings using the selected provider."""

        model = (
            self.default()
            if provider is None
            else self.get(provider)
        )

        return await model.embed(text, **kwargs)

    def select_default(
        self,
        preferred: str = "qwen3:14b",
    ) -> str:
        """Select the preferred default provider if available.

        Falls back to the first registered provider when the preferred
        model is not present.
        """
        if not self._providers:
            raise RuntimeError("No model providers are registered.")

        if preferred in self._providers:
            self._default_provider = preferred
        elif self._default_provider not in self._providers:
            self._default_provider = next(iter(self._providers))

        return self._default_provider

    def supports_provider(self, provider_name: str) -> bool:
        """Return whether the requested provider is available."""
        return self.has_provider(provider_name)

    async def health_check(self) -> dict[str, bool]:
        """Run health checks for all providers."""

        results: dict[str, bool] = {}

        for name, provider in self._providers.items():
            results[name] = await provider.health_check()

        return results