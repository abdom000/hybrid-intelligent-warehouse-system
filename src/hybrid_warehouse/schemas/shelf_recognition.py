from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from .common import WarehouseBaseModel
from .enums import ShelfStatus


class ShelfPredictionResult(WarehouseBaseModel):
    shelf_id: str = Field(min_length=1)
    status: ShelfStatus
    confidence: float = Field(ge=0, le=1)
    model_version: str = Field(min_length=1)
    prediction_time: datetime
    requires_manual_review: bool

    @field_validator("prediction_time")
    @classmethod
    def prediction_time_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("prediction_time must include timezone information.")
        return value

    @model_validator(mode="after")
    def low_confidence_requires_review(self) -> "ShelfPredictionResult":
        if self.confidence < 0.60 and not self.requires_manual_review:
            raise ValueError(
                "requires_manual_review must be true when confidence is below 0.60."
            )
        return self
