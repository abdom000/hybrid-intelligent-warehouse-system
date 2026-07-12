from __future__ import annotations

import math

import pandas as pd

FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "is_weekend",
    "lag_1",
    "lag_24",
    "rolling_mean_24",
]

TARGET_COLUMN = "order_count"


def build_training_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()

    prepared["hour_sin"] = prepared["hour"].map(
        lambda value: math.sin(2 * math.pi * value / 24)
    )
    prepared["hour_cos"] = prepared["hour"].map(
        lambda value: math.cos(2 * math.pi * value / 24)
    )
    prepared["day_sin"] = prepared["day_of_week"].map(
        lambda value: math.sin(2 * math.pi * value / 7)
    )
    prepared["day_cos"] = prepared["day_of_week"].map(
        lambda value: math.cos(2 * math.pi * value / 7)
    )

    prepared["lag_1"] = prepared[TARGET_COLUMN].shift(1)
    prepared["lag_24"] = prepared[TARGET_COLUMN].shift(24)
    prepared["rolling_mean_24"] = (
        prepared[TARGET_COLUMN]
        .shift(1)
        .rolling(window=24, min_periods=24)
        .mean()
    )

    prepared = prepared.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

    if prepared.empty:
        raise ValueError(
            "Not enough historical data to build forecasting features. "
            "At least 25 hourly rows are required."
        )

    return prepared


def split_time_series(
    frame: pd.DataFrame,
    train_ratio: float = 0.80,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0.50 <= train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0.50 and 1.0.")

    split_index = int(len(frame) * train_ratio)

    if split_index <= 0 or split_index >= len(frame):
        raise ValueError("Time-series split produced an empty partition.")

    train = frame.iloc[:split_index].copy()
    test = frame.iloc[split_index:].copy()

    return train, test
