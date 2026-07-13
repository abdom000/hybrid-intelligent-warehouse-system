from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from hybrid_warehouse.schemas import ExpertSystemFacts, ExpertSystemResult, RejectedRobot
from hybrid_warehouse.schemas.expert_system import Rule, RuleCondition

from .knowledge_base import MivarKnowledgeBase

ORDER_REJECTED = "order_rejected"
MANUAL_REVIEW_REQUIRED = "manual_review_required"


class InferenceError(ValueError):
    """Raised when facts cannot be evaluated against the knowledge base."""


@dataclass
class InferenceOutcome:
    """Expert-system result together with a human-readable inference trace."""

    result: ExpertSystemResult
    trace: list[str] = field(default_factory=list)


def _flatten_common_facts(facts: ExpertSystemFacts) -> dict[str, Any]:
    return {
        "order.order_id": facts.order.order_id,
        "order.priority": facts.order.priority,
        "order.total_weight_kg": facts.order.total_weight_kg,
        "order.shelf_id": facts.order.shelf_id,
        "shelf.shelf_id": facts.shelf.shelf_id,
        "shelf.zone_id": facts.shelf.zone_id,
        "shelf.status": facts.shelf.status,
        "shelf.confidence": facts.shelf.confidence,
        "shelf.requires_manual_review": facts.shelf.requires_manual_review,
        "forecast.expected_orders": facts.forecast.expected_orders,
        "forecast.load_level": facts.forecast.load_level,
    }


def _resolve_value(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("fact:"):
        reference = value.removeprefix("fact:")
        if reference not in context:
            raise InferenceError(f"Fact reference '{value}' is not present in the context.")
        return context[reference]
    return value


def _condition_holds(condition: RuleCondition, context: dict[str, Any]) -> bool:
    if condition.field not in context:
        raise InferenceError(
            f"Condition field '{condition.field}' is not present in the context."
        )

    actual = context[condition.field]
    expected = _resolve_value(condition.value, context)
    operator = condition.operator

    if operator == "==":
        return actual == expected
    if operator == "!=":
        return actual != expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected

    try:
        if operator == "<":
            return actual < expected
        if operator == "<=":
            return actual <= expected
        if operator == ">":
            return actual > expected
        if operator == ">=":
            return actual >= expected
    except TypeError as error:
        raise InferenceError(
            f"Cannot compare '{condition.field}' using '{operator}': {error}"
        ) from error

    raise InferenceError(f"Unsupported operator '{operator}'.")


def _rule_fires(rule: Rule, context: dict[str, Any]) -> bool:
    return all(_condition_holds(condition, context) for condition in rule.conditions)


def _is_robot_rule(rule: Rule) -> bool:
    return any(
        condition.field.startswith("robot.")
        or (
            isinstance(condition.value, str)
            and condition.value.startswith("fact:robot.")
        )
        for condition in rule.conditions
    )


def _describe_rule(rule: Rule) -> str:
    conditions = " AND ".join(
        f"{condition.field} {condition.operator} {condition.value!r}"
        for condition in rule.conditions
    )
    actions = "; ".join(f"{action.type}: {action.reason}" for action in rule.actions)
    return f"IF {conditions} THEN {actions}"


class MivarInferenceEngine:
    """Forward-chaining inference over the mivar production rules.

    Global rules (order, shelf, forecast scope) are evaluated once per
    decision; robot-scoped rules are evaluated for every candidate robot.
    Every fired rule is recorded so each decision can be explained.
    """

    def __init__(self, knowledge_base: MivarKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def evaluate(self, facts: ExpertSystemFacts) -> InferenceOutcome:
        rules = self.knowledge_base.active_rules
        global_rules = [rule for rule in rules if not _is_robot_rule(rule)]
        robot_rules = [rule for rule in rules if _is_robot_rule(rule)]

        common_context = _flatten_common_facts(facts)
        trace: list[str] = [
            f"Facts received for order {facts.order.order_id}: "
            f"{len(facts.robots)} candidate robots, shelf {facts.shelf.shelf_id} "
            f"({facts.shelf.status}, confidence {facts.shelf.confidence:.2f}), "
            f"forecast load '{facts.forecast.load_level}'."
        ]

        applied_rules: list[str] = []
        decision_constraints: list[str] = []

        def add_constraint(constraint: str) -> None:
            if constraint not in decision_constraints:
                decision_constraints.append(constraint)

        for rule in global_rules:
            if not _rule_fires(rule, common_context):
                continue
            applied_rules.append(rule.rule_id)
            trace.append(f"Rule {rule.rule_id} fired: {_describe_rule(rule)}")
            for action in rule.actions:
                if action.type == "reject_order":
                    add_constraint(ORDER_REJECTED)
                    add_constraint(f"order_rejected_reason:{action.reason}")
                elif action.type == "require_manual_review":
                    add_constraint(MANUAL_REVIEW_REQUIRED)
                elif action.type == "add_constraint":
                    add_constraint(action.reason)

        eligible_robot_ids: list[str] = []
        rejected_robots: list[RejectedRobot] = []

        for robot in facts.robots:
            robot_context = {
                **common_context,
                "robot.robot_id": robot.robot_id,
                "robot.status": robot.status,
                "robot.battery_level": robot.battery_level,
                "robot.maximum_load_kg": robot.maximum_load_kg,
                "robot.current_zone_id": robot.current_zone_id,
                "robot.current_workload": robot.current_workload,
            }

            reasons: list[str] = []
            fired_rule_ids: list[str] = []

            for rule in robot_rules:
                if not _rule_fires(rule, robot_context):
                    continue
                fired_rule_ids.append(rule.rule_id)
                if rule.rule_id not in applied_rules:
                    applied_rules.append(rule.rule_id)
                for action in rule.actions:
                    if action.type == "reject_robot":
                        reasons.append(action.reason)
                    elif action.type == "add_constraint":
                        add_constraint(action.reason)

            if reasons:
                rejected_robots.append(
                    RejectedRobot(
                        robot_id=robot.robot_id,
                        reasons=reasons,
                        applied_rules=fired_rule_ids,
                    )
                )
                trace.append(
                    f"Robot {robot.robot_id} rejected by "
                    f"{', '.join(fired_rule_ids)}: {'; '.join(reasons)}"
                )
            else:
                eligible_robot_ids.append(robot.robot_id)
                trace.append(f"Robot {robot.robot_id} passed all robot rules.")

        trace.append(
            f"Inference finished: {len(eligible_robot_ids)} eligible robots, "
            f"{len(rejected_robots)} rejected, constraints: "
            f"{decision_constraints or ['none']}."
        )

        result = ExpertSystemResult(
            order_id=facts.order.order_id,
            eligible_robot_ids=eligible_robot_ids,
            rejected_robots=rejected_robots,
            applied_rules=applied_rules,
            decision_constraints=decision_constraints,
            evaluated_at=datetime.now(timezone.utc),
        )
        return InferenceOutcome(result=result, trace=trace)
