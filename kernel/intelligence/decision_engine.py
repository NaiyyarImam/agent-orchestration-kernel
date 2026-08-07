"""Deterministic Decision Engine for the Kernel Intelligence Layer.

The DecisionEngine converts an Intent and its Reasoning into a final
Decision about what the Kernel should do next. It never executes work,
never calls adapters or the Executive Engine, and makes no LLM or
network calls; it only decides. The rule set is data-driven and
evaluated in a fixed order so a future semantic reasoning system can
influence decisions without changing the public API.
"""

from __future__ import annotations

from typing import Final

from kernel.intelligence.decision import (
    ASK_CLARIFICATION,
    ASK_CONFIRMATION,
    DEFER,
    EXECUTE,
    NOOP,
    REJECT,
    VALID_ACTIONS,
    Decision,
)
from kernel.intelligence.intent import Intent
from kernel.intelligence.reasoning import Reasoning

HIGH_CONFIDENCE_THRESHOLD: Final[float] = 0.7

# Capabilities considered unsafe; reasoning for them is always rejected.
UNSAFE_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"system", "admin", "exec", "delete"}
)

# Capabilities considered deferred; reasoning for them is always pushed back.
DEFERRED_CAPABILITIES: Final[frozenset[str]] = frozenset(
    {"background", "scheduled", "defer"}
)

ACTION_EXPLANATIONS: Final[dict[str, str]] = {
    EXECUTE: "Executing the intent directly.",
    ASK_CONFIRMATION: "Asking the user to confirm before executing.",
    ASK_CLARIFICATION: "Asking the user to clarify the intent.",
    REJECT: "Rejecting the intent as unsafe.",
    DEFER: "Deferring the intent to a later time.",
    NOOP: "Taking no action.",
}


class DecisionEngine:
    """Deterministic rule-based intent-to-action decision maker."""

    def decide(self, intent: Intent | None, reasoning: Reasoning | None) -> Decision:
        """Produce a final Decision for the given intent and reasoning.

        Rule order: missing intent -> noop, unsafe capability -> reject,
        deferred capability -> defer, low confidence -> ask_clarification,
        confirmation required -> ask_confirmation, otherwise execute.
        """
        if intent is None:
            return Decision(
                action=NOOP,
                confidence=0.0,
                requires_confirmation=False,
                explanation=self.explain(NOOP),
            )

        if reasoning is None:
            raise ValueError("reasoning is required")

        if reasoning.capability in UNSAFE_CAPABILITIES:
            action = REJECT
        elif reasoning.capability in DEFERRED_CAPABILITIES:
            action = DEFER
        elif intent.confidence < HIGH_CONFIDENCE_THRESHOLD:
            action = ASK_CLARIFICATION
        elif reasoning.requires_confirmation:
            action = ASK_CONFIRMATION
        else:
            action = EXECUTE

        return Decision(
            action=action,
            confidence=intent.confidence,
            requires_confirmation=action == ASK_CONFIRMATION,
            explanation=self._compose(
                action, intent.name, reasoning.capability, intent.confidence
            ),
            metadata={
                "intent": intent.name,
                "capability": reasoning.capability,
                "priority": reasoning.priority,
            },
        )

    def supports(self, action: str) -> bool:
        """Return True if the action is a supported decision outcome."""
        return action in VALID_ACTIONS

    def explain(self, action: str) -> str:
        """Return the canned explanation for a decision action."""
        try:
            return ACTION_EXPLANATIONS[action]
        except KeyError:
            raise ValueError(f"Unknown decision action '{action}'") from None

    async def health_check(self) -> bool:
        """Return True while the engine is operational."""
        return True

    def _compose(
        self, action: str, intent_name: str, capability: str, confidence: float
    ) -> str:
        """Build a short human-readable justification for the decision."""
        return (
            f"{self.explain(action)} Intent '{intent_name}' resolved to "
            f"capability '{capability}' with confidence {confidence}."
        )
