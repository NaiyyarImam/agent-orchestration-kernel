"""Core Proactive Intelligence Engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.proactive.opportunity import Opportunity, OpportunitySeverity
from kernel.proactive.proactive_rule import ProactiveRule, RuleAction
from kernel.proactive.proactive_signal import ProactiveSignal
from kernel.proactive.suggestion import Suggestion, SuggestionPriority


@dataclass(slots=True)
class ProactiveEngine:
    """Evaluates proactive signals against registered rules."""

    rules: list[ProactiveRule] = field(default_factory=list)

    def register_rule(self, rule: ProactiveRule) -> None:
        """Register a rule and maintain priority order."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)

    def evaluate(
        self,
        signal: ProactiveSignal,
    ) -> tuple[list[Suggestion], list[Opportunity]]:
        """Evaluate a signal and return generated suggestions and opportunities."""
        suggestions: list[Suggestion] = []
        opportunities: list[Opportunity] = []

        for rule in self.rules:
            if not rule.applies_to(signal.signal_type.value, signal.confidence):
                continue

            if rule.action is RuleAction.SUGGEST:
                suggestions.append(
                    Suggestion(
                        title=rule.name,
                        reason=rule.description,
                        priority=SuggestionPriority.MEDIUM,
                        confidence=signal.confidence,
                        metadata={"signal_id": signal.signal_id},
                    )
                )
            elif rule.action is RuleAction.OPPORTUNITY:
                opportunities.append(
                    Opportunity(
                        title=rule.name,
                        description=rule.description,
                        severity=OpportunitySeverity.MEDIUM,
                        confidence=signal.confidence,
                        metadata={"signal_id": signal.signal_id},
                    )
                )

        return suggestions, opportunities