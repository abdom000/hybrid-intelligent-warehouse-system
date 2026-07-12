from __future__ import annotations

from datetime import datetime, timezone

from hybrid_warehouse.schemas import (
    ForecastResult,
    Order,
    Robot,
    Shelf,
    ShelfPredictionResult,
)
from hybrid_warehouse.schemas.expert_system import (
    ExpertSystemFacts,
    ForecastFacts,
    OrderFacts,
    RobotFacts,
    ShelfFacts,
)


class MLIntegrationError(ValueError):
    """Raised when ML outputs cannot be converted into expert-system facts."""


def build_expert_system_facts(
    *,
    order: Order,
    robots: list[Robot],
    shelf: Shelf,
    shelf_prediction: ShelfPredictionResult,
    forecast: ForecastResult,
    generated_at: datetime | None = None,
) -> ExpertSystemFacts:
    if shelf.shelf_id != order.shelf_id:
        raise MLIntegrationError(
            "The supplied shelf does not match the order shelf_id."
        )

    if shelf_prediction.shelf_id != order.shelf_id:
        raise MLIntegrationError(
            "The shelf prediction does not match the order shelf_id."
        )

    if not robots:
        raise MLIntegrationError(
            "At least one robot is required to build expert-system facts."
        )

    robot_ids = [robot.robot_id for robot in robots]

    if len(robot_ids) != len(set(robot_ids)):
        raise MLIntegrationError(
            "Robot identifiers must be unique."
        )

    fact_time = generated_at or datetime.now(timezone.utc)

    if fact_time.tzinfo is None or fact_time.utcoffset() is None:
        raise MLIntegrationError(
            "generated_at must include timezone information."
        )

    return ExpertSystemFacts(
        order=OrderFacts(
            order_id=order.order_id,
            priority=str(order.priority),
            total_weight_kg=order.total_weight_kg,
            shelf_id=order.shelf_id,
        ),
        robots=[
            RobotFacts(
                robot_id=robot.robot_id,
                battery_level=robot.battery_level,
                maximum_load_kg=robot.maximum_load_kg,
                current_zone_id=robot.current_zone_id,
                current_workload=robot.current_workload,
                status=str(robot.status),
            )
            for robot in robots
        ],
        shelf=ShelfFacts(
            shelf_id=shelf.shelf_id,
            zone_id=shelf.zone_id,
            status=str(shelf_prediction.status),
            confidence=shelf_prediction.confidence,
            requires_manual_review=(
                shelf_prediction.requires_manual_review
            ),
        ),
        forecast=ForecastFacts(
            expected_orders=forecast.expected_orders,
            load_level=str(forecast.load_level),
        ),
        generated_at=fact_time,
    )
