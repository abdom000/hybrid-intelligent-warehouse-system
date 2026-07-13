from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from hybrid_warehouse.schemas import Rule, RuleReloadResult


class KnowledgeBaseError(ValueError):
    """Raised when the knowledge base cannot be loaded or extended."""


SUPPORTED_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "in", "not_in"}
SUPPORTED_ACTION_TYPES = {
    "reject_robot",
    "reject_order",
    "require_manual_review",
    "add_constraint",
}


def _load_json(path: Path) -> Any:
    if not path.is_file():
        raise KnowledgeBaseError(f"Knowledge base file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise KnowledgeBaseError(f"Invalid JSON in {path}: {error}") from error


class MivarKnowledgeBase:
    """Mivar (VSO) knowledge base with hot-reloadable production rules.

    The base combines two artifacts:

    - ``mivar_vso.json`` — the Thing-Property-Relation model of the domain;
    - ``rules.json`` — production rules in the IF...THEN format.

    Rules may only reference properties registered in the VSO model, which
    keeps the rule set consistent with the declared domain vocabulary.
    Rules can be reloaded or appended at runtime without restarting the
    system; an invalid rule is rejected while valid rules keep working.
    """

    def __init__(self, *, vso_path: str | Path, rules_path: str | Path) -> None:
        self._vso_path = Path(vso_path)
        self._rules_path = Path(rules_path)
        self._lock = threading.RLock()

        self._vso = self._load_vso()
        self._property_ids = self._collect_property_ids(self._vso)

        self._rules: list[Rule] = []
        result = self.reload_rules()
        if not result.success:
            raise KnowledgeBaseError(
                f"Initial rule load failed: {result.errors}"
            )

    # -- VSO model ---------------------------------------------------------

    def _load_vso(self) -> dict[str, Any]:
        vso = _load_json(self._vso_path)
        if not isinstance(vso, dict) or "things" not in vso:
            raise KnowledgeBaseError(
                f"VSO model in {self._vso_path} must be an object with a 'things' list."
            )
        return vso

    @staticmethod
    def _collect_property_ids(vso: dict[str, Any]) -> set[str]:
        property_ids: set[str] = set()
        for thing in vso.get("things", []):
            for prop in thing.get("properties", []):
                property_ids.add(prop["property_id"])
        return property_ids

    @property
    def vso_model(self) -> dict[str, Any]:
        return self._vso

    @property
    def known_properties(self) -> set[str]:
        return set(self._property_ids)

    # -- rule validation ---------------------------------------------------

    def _validate_rule_semantics(self, rule: Rule) -> list[str]:
        problems: list[str] = []
        for condition in rule.conditions:
            if condition.field not in self._property_ids:
                problems.append(
                    f"Condition field '{condition.field}' is not a registered VSO property."
                )
            if condition.operator not in SUPPORTED_OPERATORS:
                problems.append(
                    f"Operator '{condition.operator}' is not supported."
                )
            if (
                isinstance(condition.value, str)
                and condition.value.startswith("fact:")
                and condition.value.removeprefix("fact:") not in self._property_ids
            ):
                problems.append(
                    f"Fact reference '{condition.value}' is not a registered VSO property."
                )
        for action in rule.actions:
            if action.type not in SUPPORTED_ACTION_TYPES:
                problems.append(f"Action type '{action.type}' is not supported.")
        return problems

    def _parse_rules(
        self, raw_rules: list[Any]
    ) -> tuple[list[Rule], list[dict[str, Any]]]:
        rules: list[Rule] = []
        errors: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for index, raw_rule in enumerate(raw_rules):
            identifier = (
                raw_rule.get("rule_id", f"<index {index}>")
                if isinstance(raw_rule, dict)
                else f"<index {index}>"
            )
            try:
                rule = Rule.model_validate(raw_rule)
            except ValidationError as error:
                errors.append({"rule_id": identifier, "error": str(error)})
                continue

            problems = self._validate_rule_semantics(rule)
            if rule.rule_id in seen_ids:
                problems.append(f"Duplicate rule_id '{rule.rule_id}'.")
            if problems:
                errors.append({"rule_id": rule.rule_id, "error": "; ".join(problems)})
                continue

            seen_ids.add(rule.rule_id)
            rules.append(rule)

        return rules, errors

    # -- runtime operations -------------------------------------------------

    def reload_rules(self) -> RuleReloadResult:
        """Re-read rules from disk without stopping the system.

        Valid rules are swapped in atomically; invalid rules are reported
        and skipped so a bad edit cannot take the whole system down.
        """
        raw = _load_json(self._rules_path)
        if not isinstance(raw, list):
            raise KnowledgeBaseError(
                f"Rules file {self._rules_path} must contain a JSON list."
            )

        rules, errors = self._parse_rules(raw)
        with self._lock:
            self._rules = sorted(rules, key=lambda rule: -rule.priority)

        return RuleReloadResult(
            success=len(errors) == 0,
            loaded_rules=len(rules),
            rejected_rules=len(errors),
            errors=errors,
            reloaded_at=datetime.now(timezone.utc),
        )

    def add_rule(self, raw_rule: dict[str, Any]) -> RuleReloadResult:
        """Append a new rule to the knowledge base at runtime.

        The rule is validated first; only a valid rule is persisted to
        ``rules.json`` and activated. This implements evolutionary
        knowledge-base extension without a system restart.
        """
        parsed, errors = self._parse_rules([raw_rule])
        if errors:
            return RuleReloadResult(
                success=False,
                loaded_rules=len(self._rules),
                rejected_rules=1,
                errors=errors,
                reloaded_at=datetime.now(timezone.utc),
            )

        new_rule = parsed[0]
        with self._lock:
            if any(rule.rule_id == new_rule.rule_id for rule in self._rules):
                return RuleReloadResult(
                    success=False,
                    loaded_rules=len(self._rules),
                    rejected_rules=1,
                    errors=[
                        {
                            "rule_id": new_rule.rule_id,
                            "error": "A rule with this rule_id already exists.",
                        }
                    ],
                    reloaded_at=datetime.now(timezone.utc),
                )

            raw = _load_json(self._rules_path)
            raw.append(new_rule.model_dump(mode="json"))
            self._rules_path.write_text(
                json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            self._rules = sorted(
                [*self._rules, new_rule], key=lambda rule: -rule.priority
            )

        return RuleReloadResult(
            success=True,
            loaded_rules=len(self._rules),
            rejected_rules=0,
            errors=[],
            reloaded_at=datetime.now(timezone.utc),
        )

    @property
    def rules(self) -> list[Rule]:
        with self._lock:
            return list(self._rules)

    @property
    def active_rules(self) -> list[Rule]:
        with self._lock:
            return [rule for rule in self._rules if rule.active]
