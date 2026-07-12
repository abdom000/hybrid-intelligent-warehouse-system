from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .features import FEATURE_COLUMNS, TARGET_COLUMN, split_time_series


@dataclass(frozen=True)
class ForecastingMetrics:
    train_rows: int
    test_rows: int
    mae: float
    rmse: float
    r2: float
    baseline_mae: float
    improvement_over_baseline_percent: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class OrderForecastingModel:
    def __init__(
        self,
        *,
        n_estimators: int = 300,
        random_state: int = 42,
        min_samples_leaf: int = 2,
    ) -> None:
        self.estimator = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            min_samples_leaf=min_samples_leaf,
            n_jobs=-1,
        )
        self.is_fitted = False

    def fit(self, training_frame: pd.DataFrame) -> None:
        self.estimator.fit(
            training_frame[FEATURE_COLUMNS],
            training_frame[TARGET_COLUMN],
        )
        self.is_fitted = True

    def predict(self, feature_frame: pd.DataFrame) -> list[float]:
        if not self.is_fitted:
            raise RuntimeError("The forecasting model must be fitted before prediction.")

        predictions = self.estimator.predict(feature_frame[FEATURE_COLUMNS])
        return [max(0.0, float(value)) for value in predictions]

    def save(self, path: str | Path) -> None:
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted forecasting model.")

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, output_path)

    @classmethod
    def load(cls, path: str | Path) -> "OrderForecastingModel":
        model_path = Path(path)
        if not model_path.exists():
            raise FileNotFoundError(f"Forecasting model not found: {model_path}")

        loaded = joblib.load(model_path)
        if not isinstance(loaded, cls):
            raise TypeError("The loaded artifact is not an OrderForecastingModel.")

        return loaded


def train_and_evaluate(
    prepared_frame: pd.DataFrame,
    train_ratio: float = 0.80,
) -> tuple[OrderForecastingModel, ForecastingMetrics]:
    train_frame, test_frame = split_time_series(prepared_frame, train_ratio)

    model = OrderForecastingModel()
    model.fit(train_frame)

    predictions = model.predict(test_frame)
    actual = test_frame[TARGET_COLUMN].astype(float)

    baseline_predictions = test_frame["lag_24"].astype(float)

    mae = float(mean_absolute_error(actual, predictions))
    rmse = float(mean_squared_error(actual, predictions) ** 0.5)
    r2 = float(r2_score(actual, predictions))
    baseline_mae = float(mean_absolute_error(actual, baseline_predictions))

    if baseline_mae == 0:
        improvement = 0.0
    else:
        improvement = ((baseline_mae - mae) / baseline_mae) * 100

    metrics = ForecastingMetrics(
        train_rows=len(train_frame),
        test_rows=len(test_frame),
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        r2=round(r2, 4),
        baseline_mae=round(baseline_mae, 4),
        improvement_over_baseline_percent=round(improvement, 2),
    )

    return model, metrics


def model_metadata(model: OrderForecastingModel) -> dict[str, Any]:
    return {
        "model_type": type(model.estimator).__name__,
        "feature_columns": FEATURE_COLUMNS,
        "is_fitted": model.is_fitted,
    }
