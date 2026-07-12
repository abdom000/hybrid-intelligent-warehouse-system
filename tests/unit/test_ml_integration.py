from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hybrid_warehouse.integration import (
    MLIntegrationError,
    MLIntegrationService,
    build_expert_system_facts,
)
from hybrid_warehouse.schemas import (
    ForecastResult,
    Order,
    Robot,
    Shelf,
    ShelfPredictionResult,
)


def make_order() -> Order:
    return Order(
        order_id="O1",
        product_id="P1",
        shelf_id="S1",
        quantity=2,
        total_weight_kg=20.0,
        priority="urgent",
        status="pending",
        created_at=datetime.now(timezone.utc),
    )


def make_shelf(shelf_id: str = "S1") -> Shelf:
    return Shelf(
        shelf_id=shelf_id,
        zone_id="ZONE-B",
        product_id="P1",
        status="normal",
        available_quantity=30,
        last_updated_at=datetime.now(timezone.utc),
    )


def make_robot(robot_id: str = "R1") -> Robot:
    return Robot(
        robot_id=robot_id,
        current_zone_id="ZONE-A",
        battery_level=80,
        maximum_load_kg=50,
        current_load_kg=0,
        current_workload=0,
        status="available",
        updated_at=datetime.now(timezone.utc),
    )


def make_shelf_prediction(
    shelf_id: str = "S1",
) -> ShelfPredictionResult:
    return ShelfPredictionResult(
        shelf_id=shelf_id,
        status="normal",
        confidence=0.95,
        model_version="test-1.0",
        prediction_time=datetime.now(timezone.utc),
        requires_manual_review=False,
    )


def make_forecast() -> ForecastResult:
    return ForecastResult(
        forecast_time=datetime.now(timezone.utc),
        forecast_horizon_minutes=60,
        expected_orders=75,
        load_level="medium",
        model_version="test-1.0",
        generated_at=datetime.now(timezone.utc),
    )


def test_build_expert_system_facts_successfully() -> None:
    facts = build_expert_system_facts(
        order=make_order(),
        robots=[make_robot()],
        shelf=make_shelf(),
        shelf_prediction=make_shelf_prediction(),
        forecast=make_forecast(),
    )

    assert facts.order.order_id == "O1"
    assert facts.shelf.shelf_id == "S1"
    assert facts.robots[0].robot_id == "R1"
    assert facts.forecast.expected_orders == 75


def test_rejects_mismatched_shelf() -> None:
    with pytest.raises(
        MLIntegrationError,
        match="supplied shelf",
    ):
        build_expert_system_facts(
            order=make_order(),
            robots=[make_robot()],
            shelf=make_shelf("S2"),
            shelf_prediction=make_shelf_prediction(),
            forecast=make_forecast(),
        )


def test_rejects_mismatched_prediction() -> None:
    with pytest.raises(
        MLIntegrationError,
        match="shelf prediction",
    ):
        build_expert_system_facts(
            order=make_order(),
            robots=[make_robot()],
            shelf=make_shelf(),
            shelf_prediction=make_shelf_prediction("S2"),
            forecast=make_forecast(),
        )


def test_rejects_empty_robot_list() -> None:
    with pytest.raises(
        MLIntegrationError,
        match="At least one robot",
    ):
        build_expert_system_facts(
            order=make_order(),
            robots=[],
            shelf=make_shelf(),
            shelf_prediction=make_shelf_prediction(),
            forecast=make_forecast(),
        )


def test_rejects_duplicate_robot_ids() -> None:
    with pytest.raises(
        MLIntegrationError,
        match="identifiers must be unique",
    ):
        build_expert_system_facts(
            order=make_order(),
            robots=[make_robot(), make_robot()],
            shelf=make_shelf(),
            shelf_prediction=make_shelf_prediction(),
            forecast=make_forecast(),
        )


def test_service_returns_valid_expert_system_facts() -> None:
    service = MLIntegrationService()

    facts = service.build_facts(
        order=make_order(),
        robots=[make_robot("R1"), make_robot("R2")],
        shelf=make_shelf(),
        shelf_prediction=make_shelf_prediction(),
        forecast=make_forecast(),
    )

    assert len(facts.robots) == 2
    assert facts.forecast.load_level == "medium"
