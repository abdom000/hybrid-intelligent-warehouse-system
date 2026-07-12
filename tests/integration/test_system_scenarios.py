import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hybrid_warehouse.integration import (
    MLIntegrationError,
    build_expert_system_facts,
)
from hybrid_warehouse.schemas import (
    ForecastResult,
    Order,
    Robot,
    Shelf,
    ShelfPredictionResult,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOCK_DIR = PROJECT_ROOT / "data" / "mock"


def load_models(filename: str, model_type):
    payload = json.loads((MOCK_DIR / filename).read_text(encoding="utf-8"))
    return [model_type.model_validate(item) for item in payload]


def build_forecast() -> ForecastResult:
    now = datetime.now(timezone.utc)
    return ForecastResult(
        forecast_time=now,
        forecast_horizon_minutes=60,
        expected_orders=24,
        load_level="low",
        model_version="scenario-forecast-1.0",
        generated_at=now,
    )


def build_prediction(
    shelf_id: str,
    *,
    confidence: float = 0.95,
    status: str = "normal",
    requires_manual_review: bool = False,
) -> ShelfPredictionResult:
    return ShelfPredictionResult(
        shelf_id=shelf_id,
        status=status,
        confidence=confidence,
        model_version="scenario-shelf-1.0",
        prediction_time=datetime.now(timezone.utc),
        requires_manual_review=requires_manual_review,
    )


def load_matching_entities():
    orders = load_models("orders.json", Order)
    robots = load_models("robots.json", Robot)
    shelves = load_models("shelves.json", Shelf)

    order = orders[0]
    shelf = next(item for item in shelves if item.shelf_id == order.shelf_id)
    return order, robots, shelf


def test_normal_scenario_builds_expert_system_facts() -> None:
    order, robots, shelf = load_matching_entities()

    facts = build_expert_system_facts(
        order=order,
        robots=robots,
        shelf=shelf,
        shelf_prediction=build_prediction(shelf.shelf_id),
        forecast=build_forecast(),
    )

    assert facts.order.order_id == order.order_id
    assert facts.shelf.shelf_id == order.shelf_id
    assert len(facts.robots) == len(robots)
    assert facts.shelf.requires_manual_review is False


def test_unknown_shelf_scenario_requires_manual_review() -> None:
    order, robots, shelf = load_matching_entities()

    facts = build_expert_system_facts(
        order=order,
        robots=robots,
        shelf=shelf,
        shelf_prediction=build_prediction(
            shelf.shelf_id,
            confidence=0.0,
            status="unknown",
            requires_manual_review=True,
        ),
        forecast=build_forecast(),
    )

    assert facts.shelf.status == "unknown"
    assert facts.shelf.confidence == pytest.approx(0.0)
    assert facts.shelf.requires_manual_review is True


def test_mismatched_shelf_prediction_is_rejected() -> None:
    order, robots, shelf = load_matching_entities()

    with pytest.raises(MLIntegrationError):
        build_expert_system_facts(
            order=order,
            robots=robots,
            shelf=shelf,
            shelf_prediction=build_prediction("S-NOT-THE-TARGET"),
            forecast=build_forecast(),
        )


def test_empty_robot_list_is_rejected() -> None:
    order, _, shelf = load_matching_entities()

    with pytest.raises(MLIntegrationError):
        build_expert_system_facts(
            order=order,
            robots=[],
            shelf=shelf,
            shelf_prediction=build_prediction(shelf.shelf_id),
            forecast=build_forecast(),
        )


def test_duplicate_robot_ids_are_rejected() -> None:
    order, robots, shelf = load_matching_entities()

    duplicate_candidates = [robots[0], robots[0]]

    with pytest.raises(MLIntegrationError):
        build_expert_system_facts(
            order=order,
            robots=duplicate_candidates,
            shelf=shelf,
            shelf_prediction=build_prediction(shelf.shelf_id),
            forecast=build_forecast(),
        )
