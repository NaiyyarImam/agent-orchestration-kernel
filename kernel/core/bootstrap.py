

"""Bootstrap module for the JARVIS Kernel.

Responsible for constructing and wiring together all Kernel components.
"""

from __future__ import annotations

from pathlib import Path

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.config.config_manager import ConfigManager
from kernel.events.in_memory_event_bus import InMemoryEventBus
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.memory.memory_manager import MemoryManager
from kernel.models.model_manager import ModelManager
from kernel.models.ollama_provider import OllamaProvider
from kernel.security.security_manager import SecurityManager
from kernel.storage.sqlite_memory_store import SQLiteMemoryStore
from kernel.storage.storage_manager import StorageManager
from kernel.tools.tool_registry import ToolRegistry
from kernel.workflow.workflow_manager import WorkflowManager


class Bootstrap:
    """Build and expose a fully wired JARVIS Kernel."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def build(self) -> ExecutiveEngine:
        config = ConfigManager()

        storage = StorageManager(config.storage.root)

        memory_store = SQLiteMemoryStore(
            config.storage.database
        )

        memory = MemoryManager(memory_store)

        models = ModelManager()

        # Temporary provider used only for model discovery.
        discovery_provider = OllamaProvider(
            model=config.ollama.default_model,
            base_url=config.ollama.base_url,
        )

        try:
            discovered_models = discovery_provider.available_models_sync()
        except Exception as exc:
            raise RuntimeError(
                "Unable to discover installed Ollama models. "
                "Ensure the Ollama server is running."
            ) from exc

        if not discovered_models:
            raise RuntimeError(
                "No Ollama models were found. Install at least one model with 'ollama pull'."
            )

        for model_name in discovered_models:
            models.register(
                OllamaProvider(
                    model=model_name,
                    base_url=config.ollama.base_url,
                )
            )

        models.select_default(config.ollama.default_model)

        tools = ToolRegistry()

        adapters = CapabilityAdapterManager()

        workflows = WorkflowManager()

        events = InMemoryEventBus()

        security = SecurityManager()

        engine = ExecutiveEngine(
            config=config,
            memory=memory,
            models=models,
            tools=tools,
            adapters=adapters,
            workflows=workflows,
            events=events,
            security=security,
        )

        return engine