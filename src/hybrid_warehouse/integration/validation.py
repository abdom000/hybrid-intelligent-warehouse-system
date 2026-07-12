from __future__ import annotations

from hybrid_warehouse.schemas import ExpertSystemFacts


def validate_expert_system_facts(facts: ExpertSystemFacts) -> None:
    if not facts.robots:
        raise ValueError(
            "Expert-system facts must contain at least one robot."
        )

    robot_ids = [robot.robot_id for robot in facts.robots]
    if len(robot_ids) != len(set(robot_ids)):
        raise ValueError(
            "Expert-system facts contain duplicate robot identifiers."
        )

    if facts.order.shelf_id != facts.shelf.shelf_id:
        raise ValueError(
            "Order facts and shelf facts must reference the same shelf."
        )

    if facts.shelf.requires_manual_review and facts.shelf.confidence >= 0.60:
        if facts.shelf.status != "unknown":
            raise ValueError(
                "Manual review with confidence >= 0.60 is only valid "
                "for unknown shelf status."
            )
