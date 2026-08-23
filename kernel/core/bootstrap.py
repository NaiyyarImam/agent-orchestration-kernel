"""Bootstrap module for the JARVIS Kernel.

Responsible for constructing and wiring together all Kernel components.
"""

from __future__ import annotations

from pathlib import Path

from kernel.adapters.capability_adapter_manager import CapabilityAdapterManager
from kernel.adapters.research_adapter import ResearchAdapter
from kernel.adapters.coding_adapter import CodingAdapter
from kernel.adapters.browser_adapter import BrowserAdapter
from kernel.adapters.workspace_adapter import WorkspaceAdapter
from kernel.adapters.voice_adapter import VoiceAdapter
from kernel.adapters.memory_adapter import MemoryAdapter
from kernel.backends.local_research_backend import LocalResearchBackend
from kernel.config.config_manager import ConfigManager
from kernel.environment.digital_twin import DigitalTwin
from kernel.events.in_memory_event_bus import InMemoryEventBus
from kernel.events.nats_bridge import NatsBridge
from kernel.executive.executive_engine import ExecutiveEngine
from kernel.task.task_manager import InMemoryTaskManager
from kernel.intelligence.context_engine import ContextEngine
from kernel.intelligence.decision_engine import DecisionEngine
from kernel.intelligence.execution_engine import ExecutionEngine
from kernel.intelligence.intent_engine import IntentEngine
from kernel.intelligence.planning_engine import PlanningEngine
from kernel.intelligence.reasoning_engine import ReasoningEngine
from kernel.memory.memory_manager import MemoryManager
from kernel.models.model_manager import ModelManager
from kernel.models.ollama_provider import OllamaProvider
from kernel.observability.observability_manager import ObservabilityManager
from kernel.recovery.recovery_manager import RecoveryManager
from kernel.security.security_manager import SecurityManager
from kernel.storage.storage_manager import StorageManager
from kernel.tools.tool_registry import ToolRegistry
from kernel.utils.logger import KernelLogger, get_logger
from kernel.workflow.workflow_manager import WorkflowManager
from kernel.policy import PolicyEngine
from kernel.interfaces.executive import PolicyService


class Bootstrap:
    """Build and expose a fully wired JARVIS Kernel."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def create_policy(self) -> PolicyService:
        """Create the default policy service for the composed Kernel."""
        return PolicyEngine()

    def build(self, *, policy: PolicyService | None = None) -> ExecutiveEngine:
        """Construct the Kernel graph using only composition-root concretes."""
        policy = policy if policy is not None else self.create_policy()
        config = ConfigManager()
        KernelLogger.configure(log_directory=config.storage.root / "logs")

        logger = get_logger("Bootstrap")
        logger.info("Initializing JARVIS Kernel components")

        storage = StorageManager(config.storage.root)

        memory_store = storage.create_memory_store(
            config.memory.backend,
            config.storage.database,
        )

        memory = MemoryManager(memory_store)

        models = ModelManager()

        models.register(
            OllamaProvider(
                model=config.ollama.default_model,
                base_url=config.ollama.base_url,
            ),
            default=True,
        )

        logger.info(
            "Default model configured: %s",
            config.ollama.default_model,
        )

        tools = ToolRegistry()

        adapters = CapabilityAdapterManager()

        research_backend = LocalResearchBackend(memory_store=memory_store)
        research_adapter = ResearchAdapter(backend=research_backend)
        adapters.register(research_adapter)
        logger.info(
            "Registered capability adapter: %s",
            research_adapter.name,
        )
        coding_adapter = CodingAdapter()
        adapters.register(coding_adapter)
        logger.info(
            "Registered capability adapter: %s",
            coding_adapter.name,
        )
        browser_adapter = BrowserAdapter()
        adapters.register(browser_adapter)
        logger.info(
            "Registered capability adapter: %s",
            browser_adapter.name,
        )
        workspace_adapter = WorkspaceAdapter(storage)
        adapters.register(workspace_adapter)
        logger.info(
            "Registered capability adapter: %s",
            workspace_adapter.name,
        )
        voice_adapter = VoiceAdapter()
        adapters.register(voice_adapter)
        logger.info(
            "Registered capability adapter: %s",
            voice_adapter.name,
        )
        memory_adapter = MemoryAdapter(memory)
        adapters.register(memory_adapter)
        logger.info(
            "Registered capability adapter: %s",
            memory_adapter.name,
        )
        logger.info(
            "Registered capability adapters will be initialized during async kernel startup"
        )

        workflows = WorkflowManager()

        if config.events.backend == "in_memory":
            events = InMemoryEventBus()
        else:
            raise ValueError(f"Unsupported event backend: {config.events.backend}")

        nats_bridge = NatsBridge(events, config.nats) if config.nats.enabled else None

        observability = ObservabilityManager() if config.observability.enabled else None

        security = SecurityManager()

        context_engine = ContextEngine()
        intent_engine = IntentEngine()
        reasoning_engine = ReasoningEngine()
        decision_engine = DecisionEngine()
        planning_engine = PlanningEngine()
        execution_engine = ExecutionEngine(capabilities=adapters)

        digital_twin = DigitalTwin()
        recovery = RecoveryManager()

        logger.info(
            "Intelligence engines configured: context, intent, reasoning, "
            "decision, planning, execution; optional integrations: "
            "digital twin, recovery"
        )

        tasks = InMemoryTaskManager(events=events)

        engine = ExecutiveEngine(
            config=config,
            memory=memory,
            models=models,
            tools=tools,
            adapters=adapters,
            workflows=workflows,
            events=events,
            tasks=tasks,
            observability=observability,
            security=security,
            policy=policy,
            context_engine=context_engine,
            intent_engine=intent_engine,
            reasoning_engine=reasoning_engine,
            decision_engine=decision_engine,
            planning_engine=planning_engine,
            execution_engine=execution_engine,
            recovery=recovery,
            digital_twin=digital_twin,
            nats_bridge=nats_bridge,
        )

        logger.info("Bootstrap completed successfully")

        return engine
