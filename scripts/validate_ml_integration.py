from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.integration import MLIntegrationService  # noqa: E402
from hybrid_warehouse.schemas import (  # noqa: E402
    ForecastResult,
    Order,
    Robot,
    Shelf,
    ShelfPredictionResult,
)

MOCK_DIR = PROJECT_ROOT / "data" / "mock"
REPORT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_integration_report.json"
)


def load_json(filename: str):
    return json.loads(
        (MOCK_DIR / filename).read_text(encoding="utf-8")
    )


def main() -> None:
    orders = [Order.model_validate(item) for item in load_json("orders.json")]
    robots = [Robot.model_validate(item) for item in load_json("robots.json")]
    shelves = [Shelf.model_validate(item) for item in load_json("shelves.json")]

    order = orders[0]
    shelf = next(
        item for item in shelves if item.shelf_id == order.shelf_id
    )

    shelf_prediction = ShelfPredictionResult(
        shelf_id=shelf.shelf_id,
        status=shelf.status,
        confidence=0.95,
        model_version="integration-validation-1.0",
        prediction_time=datetime.now(timezone.utc),
        requires_manual_review=False,
    )

    forecast = ForecastResult(
        forecast_time=datetime.now(timezone.utc),
        forecast_horizon_minutes=60,
        expected_orders=72,
        load_level="medium",
        model_version="integration-validation-1.0",
        generated_at=datetime.now(timezone.utc),
    )

    service = MLIntegrationService()
    facts = service.build_facts(
        order=order,
        robots=robots,
        shelf=shelf,
        shelf_prediction=shelf_prediction,
        forecast=forecast,
    )

    payload = {
        "status": "passed",
        "order_id": facts.order.order_id,
        "shelf_id": facts.shelf.shelf_id,
        "robot_count": len(facts.robots),
        "forecast_expected_orders": facts.forecast.expected_orders,
        "forecast_load_level": facts.forecast.load_level,
        "shelf_status": facts.shelf.status,
        "requires_manual_review": facts.shelf.requires_manual_review,
        "generated_at": facts.generated_at.isoformat(),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print("ML integration validation passed.")
    print(f"Order: {facts.order.order_id}")
    print(f"Shelf: {facts.shelf.shelf_id}")
    print(f"Robots: {len(facts.robots)}")
    print(f"Forecast load: {facts.forecast.load_level}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
