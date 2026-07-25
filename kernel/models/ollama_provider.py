"""Ollama ModelProvider implementation for the JARVIS Kernel."""
from __future__ import annotations

from typing import Any
import httpx
from kernel.interfaces.model_provider import ModelProvider

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_TIMEOUT = 120.0


class OllamaProvider(ModelProvider):
    def __init__(self, model: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT):
        self._model = model
        self._base_url = base_url
        self._timeout = timeout

    @property
    def name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def timeout(self) -> float:
        return self._timeout

    @property
    def metadata(self) -> dict[str, Any]:
        """Return provider metadata."""
        return {
            "provider": "ollama",
            "model": self._model,
            "base_url": self._base_url,
            "timeout": self._timeout,
        }

    async def generate(self, messages: list[dict], **kwargs: Any) -> dict:
        """
        Generate a response from the Ollama model using OpenAI-compatible /chat/completions endpoint.
        """
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
        }
        payload.update(kwargs)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding using the configured Ollama model."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/embeddings",
                json={
                    "model": self._model,
                    "input": text,
                },
            )
            response.raise_for_status()
            data = response.json()

        if "data" in data and data["data"]:
            return data["data"][0].get("embedding", [])

        return data.get("embedding", [])

    async def health_check(self) -> bool:
        """Check whether the Ollama server is reachable."""

        url = self._native_base_url() + "/api/tags"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()

                return (
                    isinstance(data, dict)
                    and isinstance(data.get("models"), list)
                )

        except (httpx.HTTPError, httpx.RequestError):
            return False

    async def ping(self) -> bool:
        return await self.health_check()

    def _native_base_url(self) -> str:
        """Return the Ollama native API base URL."""
        return self._base_url.removesuffix("/v1")

    async def available_models(self) -> list[str]:
        """Discover installed Ollama models using the native Ollama API."""
        url = self._native_base_url() + "/api/tags"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        return [
            model["name"]
            for model in data.get("models", [])
            if "name" in model
        ]

    def available_models_sync(self) -> list[str]:
        """Synchronously discover installed Ollama models.

        This helper is intended for use during synchronous bootstrap.
        """
        url = self._native_base_url() + "/api/tags"

        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        return [
            model["name"]
            for model in data.get("models", [])
            if "name" in model
        ]

    async def model_info(self) -> dict:
        return self.metadata