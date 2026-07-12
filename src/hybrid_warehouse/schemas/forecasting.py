from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from .common import WarehouseBaseModel
from .enums import LoadLevel


class ForecastResult(WarehouseBaseModel):
    forecast_time: datetime
    forecast_horizon_minutes: int = Field(gt=0)
    expected_orders: int = Field(ge=0)
    load_level: LoadLevel
    model_version: str = Field(min_length=1)
    generated_at: datetime

    @field_validator("forecast_time", "generated_at")
    @classmethod
    def datetime_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must include timezone information.")
        return value
