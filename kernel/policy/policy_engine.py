

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from .policy_rule import PolicyRule


class PolicyEngine:
    """Evaluates policy rules for a requested intent.

    The engine is intentionally lightweight. It is responsible only for
    looking up a matching rule and returning the associated policy decision.
    Authorization, authentication, approval workflows, and execution are
    handled by other Kernel components.
    """

    DEFAULT_DENY_REASON: Final[str] = (
        "No policy rule registered for this intent."
    )

    def __init__(self, rules: Iterable[PolicyRule] | None = None) -> None:
        self._rules: dict[str, PolicyRule] = {}
        if rules is not None:
            for rule in rules:
                self.register(rule)

    def register(self, rule: PolicyRule) -> None:
        """Register or replace a policy rule for an intent."""
        if not rule.intent:
            raise ValueError("Policy intent cannot be empty.")
        self._rules[rule.intent] = rule

    def unregister(self, intent: str) -> None:
        """Remove a policy rule if it exists."""
        if not intent:
            raise ValueError("Policy intent cannot be empty.")
        self._rules.pop(intent, None)

    def get_rule(self, intent: str) -> PolicyRule | None:
        """Return the policy rule for an intent, if present."""
        if not intent:
            raise ValueError("Policy intent cannot be empty.")
        return self._rules.get(intent)

    def evaluate(self, intent: str) -> PolicyRule:
        """Return the policy decision for an intent.

        If no rule is registered, a secure default-deny rule is returned.
        """
        if not intent:
            raise ValueError("Policy intent cannot be empty.")
        rule = self.get_rule(intent)
        if rule is not None:
            return rule

        return PolicyRule(
            intent=intent,
            allowed=False,
            reason=self.DEFAULT_DENY_REASON,
        )

    def list_rules(self) -> tuple[PolicyRule, ...]:
        """Return all registered rules."""
        return tuple(self._rules.values())


    def clear(self) -> None:
        """Remove all registered policy rules."""
        self._rules.clear()

    def has_rule(self, intent: str) -> bool:
        """Return True if a rule exists for the supplied intent."""
        if not intent:
            raise ValueError("Policy intent cannot be empty.")
        return intent in self._rules

    def __contains__(self, intent: object) -> bool:
        """Support the `in` operator using policy intents."""
        return isinstance(intent, str) and intent in self._rules

    def __len__(self) -> int:
        """Return the number of registered policy rules."""
        return len(self._rules)