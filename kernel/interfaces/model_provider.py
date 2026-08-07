

"""Abstract interface for language model providers used by the JARVIS Kernel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    """Framework-agnostic interface for all LLM backends.

    Implementations may wrap Ollama, OpenAI-compatible APIs, vLLM,
    SGLang, or any future provider. The Kernel must depend only on
    this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a text completion."""

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Return an embedding vector for the supplied text."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is healthy and available."""

    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """Return provider capabilities and model metadata."""
