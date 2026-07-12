from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from hybrid_warehouse.forecasting import (
    ForecastingService,
    OrderForecastingModel,
    build_training_frame,
    split_time_series,
)


def make_history(rows: int = 72) -> pd.DataFrame:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    timestamps = [start + timedelta(hours=index) for index in range(rows)]

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "order_count": [20 + (index % 24) for index in range(rows)],
            "hour": [value.hour for value in timestamps],
            "day_of_week": [value.weekday() for value in timestamps],
            "is_weekend": [int(value.weekday() >= 5) for value in timestamps],
        }
    )


def test_build_training_frame_creates_lag_features() -> None:
    prepared = build_training_frame(make_history())

    assert not prepared.empty
    assert {"lag_1", "lag_24", "rolling_mean_24"}.issubset(prepared.columns)
    assert prepared.iloc[0]["lag_1"] == 43
    assert prepared.iloc[0]["lag_24"] == 20


def test_time_split_preserves_order() -> None:
    prepared = build_training_frame(make_history())
    train, test = split_time_series(prepared, train_ratio=0.80)

    assert train.iloc[-1]["timestamp"] < test.iloc[0]["timestamp"]


def test_model_must_be_fitted_before_prediction() -> None:
    model = OrderForecastingModel()

    with pytest.raises(RuntimeError):
        model.predict(
            pd.DataFrame(
                [
                    {
                        "hour_sin": 0.0,
                        "hour_cos": 1.0,
                        "day_sin": 0.0,
                        "day_cos": 1.0,
                        "is_weekend": 0,
                        "lag_1": 10,
                        "lag_24": 10,
                        "rolling_mean_24": 10,
                    }
                ]
            )
        )


def test_forecasting_service_returns_schema_result() -> None:
    history = make_history(96)
    prepared = build_training_frame(history)

    model = OrderForecastingModel(n_estimators=20)
    model.fit(prepared)

    service = ForecastingService(model)
    forecast_time = history.iloc[-1]["timestamp"] + timedelta(hours=1)

    result = service.forecast_next_hour(history, forecast_time)

    assert result.expected_orders >= 0
    assert result.forecast_horizon_minutes == 60
    assert result.load_level in {"low", "medium", "high"}
