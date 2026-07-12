from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from hybrid_warehouse.forecasting import (
    ForecastingService,
    OrderForecastingModel,
    build_training_frame,
    load_historical_orders,
)
from hybrid_warehouse.schemas import Order, Robot, Shelf, ShelfStatus
from hybrid_warehouse.shelf_recognition import (
    ShelfRecognitionService,
    StaticShelfPredictor,
)

from .service import MLIntegrationService


def _load_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}.")
    return data


def run_ml_end_to_end_demo(
    project_root: str | Path,
    *,
    order_id: str = "O101",
) -> dict[str, Any]:
    root = Path(project_root)
    mock_dir = root / "data" / "mock"

    orders = [
        Order.model_validate(item)
        for item in _load_json(mock_dir / "orders.json")
    ]
    robots = [
        Robot.model_validate(item)
        for item in _load_json(mock_dir / "robots.json")
    ]
    shelves = [
        Shelf.model_validate(item)
        for item in _load_json(mock_dir / "shelves.json")
    ]

    try:
        order = next(item for item in orders if item.order_id == order_id)
    except StopIteration as error:
        raise ValueError(f"Order not found: {order_id}") from error

    try:
        shelf = next(
            item for item in shelves if item.shelf_id == order.shelf_id
        )
    except StopIteration as error:
        raise ValueError(
            f"Shelf {order.shelf_id} required by order {order.order_id} was not found."
        ) from error

    history = load_historical_orders(
        mock_dir / "historical_orders.csv"
    )
    prepared = build_training_frame(history)

    forecasting_model = OrderForecastingModel(
        n_estimators=50,
        random_state=42,
        min_samples_leaf=2,
    )
    forecasting_model.fit(prepared)

    forecast_time = (
        history.iloc[-1]["timestamp"].to_pydatetime()
        + timedelta(hours=1)
    )
    forecast = ForecastingService(
        forecasting_model,
        model_version="demo-random-forest-1.0",
    ).forecast_next_hour(
        history=history,
        forecast_time=forecast_time,
    )

    shelf_service = ShelfRecognitionService(
        StaticShelfPredictor(
            status=ShelfStatus.UNKNOWN,
            confidence=0.0,
            model_version="demo-fallback-1.0",
        )
    )
    shelf_prediction = shelf_service.unavailable_image_result(
        shelf_id=shelf.shelf_id,
        model_version="demo-no-image-1.0",
    )

    facts = MLIntegrationService().build_facts(
        order=order,
        robots=robots,
        shelf=shelf,
        shelf_prediction=shelf_prediction,
        forecast=forecast,
    )

    return {
        "demo_status": "passed",
        "mode": "ml_pipeline_to_expert_system_facts",
        "limitations": [
            "No shelf images are available, so shelf recognition uses the unknown/manual-review fallback.",
            "The expert-system rule engine is not executed in this demo.",
        ],
        "order": order.model_dump(mode="json"),
        "forecast": forecast.model_dump(mode="json"),
        "shelf_prediction": shelf_prediction.model_dump(mode="json"),
        "expert_system_facts": facts.model_dump(mode="json"),
    }
