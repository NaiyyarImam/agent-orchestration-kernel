"""Model interfaces for the JARVIS Kernel.

Defines the contract for language models, their metadata, and capabilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities supported by a model."""

    chat: bool = True
    completion: bool = True
    embedding: bool = False
    vision: bool = False
    audio: bool = False
    function_calling: bool = False
    structured_output: bool = False
    custom: dict[str, bool] = field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        """Check if a capability is supported."""
        if hasattr(self, capability):
            return getattr(self, capability)
        return self.custom.get(capability, False)

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary."""
        result = {
            "chat": self.chat,
            "completion": self.completion,
            "embedding": self.embedding,
            "vision": self.vision,
            "audio": self.audio,
            "function_calling": self.function_calling,
            "structured_output": self.structured_output,
        }
        result.update(self.custom)
        return result


@dataclass(frozen=True)
class ModelMetadata:
    """Immutable metadata describing a model."""

    name: str
    provider: str
    capabilities: ModelCapabilities
    context_window: int = 4096
    max_output_tokens: int = 2048
    model_family: str = ""
    parameter_count: str = ""
    quantization: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "provider": self.provider,
            "capabilities": self.capabilities.to_dict(),
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "model_family": self.model_family,
            "parameter_count": self.parameter_count,
            "quantization": self.quantization,
            "description": self.description,
            "tags": self.tags,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelMetadata:
        """Create from dictionary."""
        caps_data = data.get("capabilities", {})
        capabilities = ModelCapabilities(
            chat=caps_data.get("chat", True),
            completion=caps_data.get("completion", True),
            embedding=caps_data.get("embedding", False),
            vision=caps_data.get("vision", False),
            audio=caps_data.get("audio", False),
            function_calling=caps_data.get("function_calling", False),
            structured_output=caps_data.get("structured_output", False),
            custom={k: v for k, v in caps_data.items() if k not in {
                "chat", "completion", "embedding", "vision", "audio",
                "function_calling", "structured_output"
            }},
        )
        return cls(
            name=data["name"],
            provider=data["provider"],
            capabilities=capabilities,
            context_window=data.get("context_window", 4096),
            max_output_tokens=data.get("max_output_tokens", 2048),
            model_family=data.get("model_family", ""),
            parameter_count=data.get("parameter_count", ""),
            quantization=data.get("quantization", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            custom=data.get("custom", {}),
        )


class Model(ABC):
    """Interface for a language model instance.

    A Model represents a single model served by a provider.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Model identifier (e.g., 'qwen3:14b')."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name (e.g., 'ollama')."""

    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Model metadata including capabilities."""

    @abstractmethod
    def supports_capability(self, capability: str) -> bool:
        """Check if model supports a capability."""

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
    async def embed(self, text: str) -> list[float]:
        """Return an embedding vector for the supplied text."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the model is healthy and available."""

    @abstractmethod
    async def get_metadata(self) -> ModelMetadata:
        """Return current model metadata (may refresh from provider)."""