from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "timestamp",
    "order_count",
    "hour",
    "day_of_week",
    "is_weekend",
}


def load_historical_orders(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Historical orders file not found: {csv_path}"
        )

    frame = pd.read_csv(csv_path)

    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="raise",
    )

    frame["order_count"] = pd.to_numeric(
        frame["order_count"],
        errors="raise",
    ).astype(int)

    frame["hour"] = pd.to_numeric(
        frame["hour"],
        errors="raise",
    ).astype(int)

    frame["day_of_week"] = pd.to_numeric(
        frame["day_of_week"],
        errors="raise",
    ).astype(int)

    weekend_values = (
        frame["is_weekend"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "true": 1,
                "false": 0,
                "1": 1,
                "0": 0,
            }
        )
    )

    if weekend_values.isna().any():
        invalid_values = sorted(
            frame.loc[
                weekend_values.isna(),
                "is_weekend",
            ]
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "is_weekend must contain only True, False, 1, or 0. "
            f"Invalid values: {invalid_values}"
        )

    frame["is_weekend"] = weekend_values.astype(int)

    if frame["timestamp"].duplicated().any():
        raise ValueError(
            "Historical order timestamps must be unique."
        )

    if (frame["order_count"] < 0).any():
        raise ValueError(
            "order_count must be non-negative."
        )

    if not frame["hour"].between(0, 23).all():
        raise ValueError(
            "hour must be between 0 and 23."
        )

    if not frame["day_of_week"].between(0, 6).all():
        raise ValueError(
            "day_of_week must be between 0 and 6."
        )

    frame = frame.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    inferred_hours = (
        frame["timestamp"]
        .dt.hour
        .astype(int)
    )

    inferred_days = (
        frame["timestamp"]
        .dt.dayofweek
        .astype(int)
    )

    inferred_weekends = (
        inferred_days >= 5
    ).astype(int)

    if not (
        frame["hour"].to_numpy()
        == inferred_hours.to_numpy()
    ).all():
        raise ValueError(
            "hour values do not match timestamp values."
        )

    if not (
        frame["day_of_week"].to_numpy()
        == inferred_days.to_numpy()
    ).all():
        raise ValueError(
            "day_of_week values do not match timestamp values."
        )

    if not (
        frame["is_weekend"].to_numpy()
        == inferred_weekends.to_numpy()
    ).all():
        raise ValueError(
            "is_weekend values do not match timestamp values."
        )

    return frame
