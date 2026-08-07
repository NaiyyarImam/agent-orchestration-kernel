"""Deterministic Reasoning Engine for the Kernel Intelligence Layer.

The ReasoningEngine converts a classified Intent into a structured
Reasoning object using a fixed, data-driven rule set. It never executes
work, never calls adapters or the Executive Engine, and makes no LLM or
network calls; it only reasons about what should happen. The rule table
is deliberately data-driven so a future semantic reasoning system can
replace the deterministic logic without changing the public API.
"""

from __future__ import annotations

from typing import Final

from kernel.intelligence.intent import Intent
from kernel.intelligence.reasoning import Reasoning

LOW: Final[str] = "LOW"
NORMAL: Final[str] = "NORMAL"
HIGH: Final[str] = "HIGH"

FALLBACK_CAPABILITY: Final[str] = "chat"

# Intent name -> (capability, priority, requires_confirmation).
# The emitted capability name is the canonical name the execution layer
# dispatches on, so it must be supported by a registered adapter
# (checked via CapabilityAdapterManager.can_handle). Memory capabilities
# therefore use the adapter-declared operation names (remember, recall,
# search_memory, forget) rather than a collapsed "memory" capability.
REASONING_RULES: Final[dict[str, tuple[str, str, bool]]] = {
    "chat": ("chat", LOW, False),
    "search_memory": ("search_memory", LOW, False),
    "remember": ("remember", LOW, False),
    "recall": ("recall", LOW, False),
    "forget": ("forget", LOW, False),
    "research": ("research", NORMAL, False),
    "code": ("coding", HIGH, False),
    "workspace": ("workspace", NORMAL, True),
    "browser": ("browser", NORMAL, False),
    "voice": ("voice", LOW, False),
}


class ReasoningEngine:
    """Deterministic rule-based intent-to-capability reasoner."""

    def reason(self, intent: Intent) -> Reasoning:
        """Produce structured reasoning for the given intent.

        Unrecognized intent names fall back to the chat capability.
        """
        if intent is None:
            raise ValueError("intent is required")
        return self._reason_for(intent.name)

    def supports(self, intent_name: str) -> bool:
        """Return True if the intent name has a reasoning rule."""
        return intent_name in REASONING_RULES

    async def health_check(self) -> bool:
        """Return True while the engine is operational."""
        return True

    def _reason_for(self, intent_name: str) -> Reasoning:
        capability, priority, requires_confirmation = REASONING_RULES.get(
            intent_name, (FALLBACK_CAPABILITY, LOW, False)
        )
        return Reasoning(
            intent_name=intent_name,
            capability=capability,
            explanation=self._explain(intent_name, capability, priority),
            priority=priority,
            requires_confirmation=requires_confirmation,
        )

    @staticmethod
    def _explain(intent_name: str, capability: str, priority: str) -> str:
        """Build a short human-readable justification for the mapping."""
        return (
            f"Intent '{intent_name}' resolved to the '{capability}' "
            f"capability with {priority} priority."
        )
