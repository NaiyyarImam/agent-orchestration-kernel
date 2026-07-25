

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from .policy_rule import PolicyRule
import fnmatch

import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


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
        self._audit_log: list[dict[str, Any]] = []
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
            self._record_audit(intent, rule)
            return rule

        wildcard_matches = [
            candidate
            for pattern, candidate in self._rules.items()
            if "*" in pattern and fnmatch.fnmatch(intent, pattern)
        ]

        if wildcard_matches:
            wildcard_matches.sort(
                key=lambda rule: (
                    -rule.priority,
                    rule.intent.count("*"),
                    -len(rule.intent),
                )
            )
            selected = wildcard_matches[0]
            self._record_audit(intent, selected)
            return selected

        decision = PolicyRule(
            intent=intent,
            allowed=False,
            reason=self.DEFAULT_DENY_REASON,
        )
        self._record_audit(intent, decision)
        return decision

    def list_rules(self) -> tuple[PolicyRule, ...]:
        """Return all registered rules."""
        return tuple(self._rules.values())


    def _record_audit(self, requested_intent: str, rule: PolicyRule) -> None:
        self._audit_log.append(
            {
                "timestamp": datetime.now(UTC),
                "requested_intent": requested_intent,
                "matched_intent": rule.intent,
                "allowed": rule.allowed,
                "requires_approval": rule.requires_approval,
                "reason": rule.reason,
                "priority": rule.priority,
            }
        )

    def audit_log(self) -> tuple[MappingProxyType[str, Any], ...]:
        """Return an immutable snapshot of the audit log."""
        return tuple(MappingProxyType(entry) for entry in self._audit_log)

    def clear_audit(self) -> None:
        """Remove all audit log entries."""
        self._audit_log.clear()


    def load_dicts(self, rules: Iterable[dict[str, Any]], *, replace: bool = True) -> None:
        """Load policy rules from an iterable of dictionaries."""
        if replace:
            self.clear()
        for data in rules:
            self.register(PolicyRule.from_dict(data))

    def load_json(self, path: str | Path, *, replace: bool = True) -> None:
        """Load policy rules from a JSON file."""
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("JSON policy file must contain a list of policy rules.")
        self.load_dicts(data, replace=replace)

    def load_yaml(self, path: str | Path, *, replace: bool = True) -> None:
        """Load policy rules from a YAML file."""
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML policy files.")
        with Path(path).open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or []
        if not isinstance(data, list):
            raise ValueError("YAML policy file must contain a list of policy rules.")
        self.load_dicts(data, replace=replace)


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