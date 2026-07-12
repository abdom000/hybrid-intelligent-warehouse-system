from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from hybrid_warehouse.schemas import ShelfStatus


@dataclass(frozen=True)
class RawShelfPrediction:
    status: ShelfStatus
    confidence: float


class ShelfStatusPredictor(Protocol):
    model_version: str

    def predict(self, image_path: Path) -> RawShelfPrediction:
        ...


class StaticShelfPredictor:
    def __init__(
        self,
        *,
        status: ShelfStatus,
        confidence: float,
        model_version: str = "static-test-1.0",
    ) -> None:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1.")

        self.status = status
        self.confidence = confidence
        self.model_version = model_version

    def predict(self, image_path: Path) -> RawShelfPrediction:
        return RawShelfPrediction(
            status=self.status,
            confidence=self.confidence,
        )
