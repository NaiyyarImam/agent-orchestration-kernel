"""Model subsystem for the JARVIS Kernel.

Exports the internal Model abstraction and public interfaces.
"""

from __future__ import annotations

from kernel.models.model_manager import ModelManager
from kernel.models.ollama_provider import OllamaProvider

__all__ = [
    "ModelManager",
    "OllamaProvider",
]