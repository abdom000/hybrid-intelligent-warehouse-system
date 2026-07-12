from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

import pandas as pd

from hybrid_warehouse.schemas import ForecastResult, LoadLevel

from .model import OrderForecastingModel


class ForecastingService:
    def __init__(
        self,
        model: OrderForecastingModel,
        *,
        model_version: str = "1.0.0",
    ) -> None:
        self.model = model
        self.model_version = model_version

    @classmethod
    def from_artifact(
        cls,
        path: str | Path,
        *,
        model_version: str = "1.0.0",
    ) -> "ForecastingService":
        return cls(
            OrderForecastingModel.load(path),
            model_version=model_version,
        )

    def forecast_next_hour(
        self,
        history: pd.DataFrame,
        forecast_time: datetime,
    ) -> ForecastResult:
        if forecast_time.tzinfo is None or forecast_time.utcoffset() is None:
            raise ValueError("forecast_time must include timezone information.")

        if len(history) < 24:
            raise ValueError("At least 24 historical hourly rows are required.")

        ordered = history.sort_values("timestamp").reset_index(drop=True)
        latest_timestamp = pd.Timestamp(ordered.iloc[-1]["timestamp"])

        if latest_timestamp.tzinfo is None:
            raise ValueError("Historical timestamps must include timezone information.")

        expected_next = latest_timestamp + pd.Timedelta(hours=1)
        requested = pd.Timestamp(forecast_time)

        if requested != expected_next:
            raise ValueError(
                "forecast_time must be exactly one hour after the latest history row."
            )

        hour = forecast_time.hour
        day_of_week = forecast_time.weekday()

        feature_row = pd.DataFrame(
            [
                {
                    "hour_sin": math.sin(2 * math.pi * hour / 24),
                    "hour_cos": math.cos(2 * math.pi * hour / 24),
                    "day_sin": math.sin(2 * math.pi * day_of_week / 7),
                    "day_cos": math.cos(2 * math.pi * day_of_week / 7),
                    "is_weekend": int(day_of_week >= 5),
                    "lag_1": float(ordered.iloc[-1]["order_count"]),
                    "lag_24": float(ordered.iloc[-24]["order_count"]),
                    "rolling_mean_24": float(
                        ordered.iloc[-24:]["order_count"].mean()
                    ),
                }
            ]
        )

        prediction = max(0, round(self.model.predict(feature_row)[0]))

        if prediction < 50:
            load_level = LoadLevel.LOW
        elif prediction < 100:
            load_level = LoadLevel.MEDIUM
        else:
            load_level = LoadLevel.HIGH

        return ForecastResult(
            forecast_time=forecast_time,
            forecast_horizon_minutes=60,
            expected_orders=prediction,
            load_level=load_level,
            model_version=self.model_version,
            generated_at=datetime.now(tz=forecast_time.tzinfo),
        )
