"""Intelligence Layer for the JARVIS Kernel.

Exports the Intent model and the rule-based IntentEngine.
"""

from __future__ import annotations

from kernel.intelligence.intent import Intent
from kernel.intelligence.intent_engine import IntentEngine

__all__ = [
    "Intent",
    "IntentEngine",
]
