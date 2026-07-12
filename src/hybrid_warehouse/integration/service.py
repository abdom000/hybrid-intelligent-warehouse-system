from __future__ import annotations

from datetime import datetime

from hybrid_warehouse.schemas import (
    ExpertSystemFacts,
    ForecastResult,
    Order,
    Robot,
    Shelf,
    ShelfPredictionResult,
)

from .facts_builder import build_expert_system_facts
from .validation import validate_expert_system_facts


class MLIntegrationService:
    def build_facts(
        self,
        *,
        order: Order,
        robots: list[Robot],
        shelf: Shelf,
        shelf_prediction: ShelfPredictionResult,
        forecast: ForecastResult,
        generated_at: datetime | None = None,
    ) -> ExpertSystemFacts:
        facts = build_expert_system_facts(
            order=order,
            robots=robots,
            shelf=shelf,
            shelf_prediction=shelf_prediction,
            forecast=forecast,
            generated_at=generated_at,
        )
        validate_expert_system_facts(facts)
        return facts
