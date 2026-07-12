from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from hybrid_warehouse.schemas import ForecastResult, ShelfPredictionResult


def aware_now() -> datetime:
    return datetime.now(timezone.utc)


def test_forecast_contract_accepts_zero_expected_orders() -> None:
    result = ForecastResult(
        forecast_time=aware_now(),
        forecast_horizon_minutes=60,
        expected_orders=0,
        load_level="low",
        model_version="test-forecast-1.0",
        generated_at=aware_now(),
    )

    assert result.expected_orders == 0


def test_forecast_contract_rejects_negative_expected_orders() -> None:
    with pytest.raises(ValidationError):
        ForecastResult(
            forecast_time=aware_now(),
            forecast_horizon_minutes=60,
            expected_orders=-1,
            load_level="low",
            model_version="test-forecast-1.0",
            generated_at=aware_now(),
        )


def test_shelf_contract_accepts_low_confidence_with_manual_review() -> None:
    result = ShelfPredictionResult(
        shelf_id="S1",
        status="unknown",
        confidence=0.59,
        model_version="test-shelf-fallback-1.0",
        prediction_time=aware_now(),
        requires_manual_review=True,
    )

    assert result.requires_manual_review is True
    assert result.confidence == pytest.approx(0.59)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_shelf_contract_rejects_confidence_outside_unit_interval(
    confidence: float,
) -> None:
    with pytest.raises(ValidationError):
        ShelfPredictionResult(
            shelf_id="S1",
            status="unknown",
            confidence=confidence,
            model_version="test-shelf-fallback-1.0",
            prediction_time=aware_now(),
            requires_manual_review=True,
        )
