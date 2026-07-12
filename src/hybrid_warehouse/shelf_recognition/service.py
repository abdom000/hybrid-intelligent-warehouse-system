from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from hybrid_warehouse.schemas import ShelfPredictionResult, ShelfStatus

from .image_loader import validate_image
from .predictor import ShelfStatusPredictor


class ShelfRecognitionService:
    def __init__(
        self,
        predictor: ShelfStatusPredictor,
        *,
        manual_review_threshold: float = 0.60,
    ) -> None:
        if not 0 < manual_review_threshold <= 1:
            raise ValueError(
                "manual_review_threshold must be greater than 0 and at most 1."
            )

        self.predictor = predictor
        self.manual_review_threshold = manual_review_threshold

    def predict(
        self,
        *,
        shelf_id: str,
        image_path: str | Path,
    ) -> ShelfPredictionResult:
        validated_path = validate_image(image_path)
        raw_prediction = self.predictor.predict(validated_path)

        requires_manual_review = (
            raw_prediction.confidence < self.manual_review_threshold
            or raw_prediction.status == ShelfStatus.UNKNOWN
        )

        return ShelfPredictionResult(
            shelf_id=shelf_id,
            status=raw_prediction.status,
            confidence=raw_prediction.confidence,
            model_version=self.predictor.model_version,
            prediction_time=datetime.now(timezone.utc),
            requires_manual_review=requires_manual_review,
        )

    def unavailable_image_result(
        self,
        *,
        shelf_id: str,
        model_version: str = "unavailable-image-1.0",
    ) -> ShelfPredictionResult:
        return ShelfPredictionResult(
            shelf_id=shelf_id,
            status=ShelfStatus.UNKNOWN,
            confidence=0.0,
            model_version=model_version,
            prediction_time=datetime.now(timezone.utc),
            requires_manual_review=True,
        )
