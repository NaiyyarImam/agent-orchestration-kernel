"""Rule-based Intent Engine for the Kernel Intelligence Layer.

The IntentEngine converts a natural-language user request into a
structured Intent object using lightweight, deterministic keyword
matching. It is intentionally free of LLM and network dependencies;
the rule set is data-driven so a future semantic routing system can
replace or augment it without changing the public API.
"""

from __future__ import annotations

from typing import Final

from kernel.intelligence.intent import Intent

FALLBACK_INTENT: Final[str] = "chat"
MATCHED_CONFIDENCE: Final[float] = 0.9
FALLBACK_CONFIDENCE: Final[float] = 0.4

# Intent name -> keywords that signal the intent.
# Order matters: the first intent whose keywords match wins.
INTENT_RULES: Final[dict[str, tuple[str, ...]]] = {
    "research": ("search", "research", "summarize", "look up", "find information"),
    "code": ("code", "python", "script", "function", "implement", "debug"),
    "memory": ("remember", "recall", "forget", "memorize", "store this"),
    "workspace": ("file", "directory", "folder", "project", "open my", "workspace"),
    "browser": ("browse", "website", "web page", "visit", "open url", "navigate"),
}


class IntentEngine:
    """Deterministic rule-based intent classifier."""

    def classify(self, text: str) -> Intent:
        """Classify a user request into a structured Intent.

        Unrecognized or empty input falls back to the chat intent.
        """
        normalized = self._normalize(text)

        if not normalized:
            return self._fallback(text)

        for intent_name, keywords in INTENT_RULES.items():
            if any(keyword in normalized for keyword in keywords):
                return Intent(
                    name=intent_name,
                    confidence=MATCHED_CONFIDENCE,
                    parameters={"text": text},
                )

        return self._fallback(text)

    def supports(self, intent_name: str) -> bool:
        """Return True if the intent name is recognized."""
        return intent_name in INTENT_RULES

    async def health_check(self) -> bool:
        """Return True while the engine is operational."""
        return True

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase and collapse whitespace for keyword matching."""
        return " ".join(text.lower().split())

    def _fallback(self, text: str) -> Intent:
        return Intent(
            name=FALLBACK_INTENT,
            confidence=FALLBACK_CONFIDENCE,
            parameters={"text": text},
        )
