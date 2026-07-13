

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

        storage = StorageManager(self.root / "storage")

        memory_store = SQLiteMemoryStore(
            storage.root / "jarvis_memory.db"
        )

        memory = MemoryManager(memory_store)

        model_provider = OllamaProvider(model="qwen3:14b")

        models = ModelManager()
        models.register(model_provider)

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