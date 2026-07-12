from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.forecasting import (  # noqa: E402
    build_training_frame,
    load_historical_orders,
    model_metadata,
    train_and_evaluate,
)

DATA_PATH = PROJECT_ROOT / "data" / "mock" / "historical_orders.csv"
MODEL_PATH = PROJECT_ROOT / "data" / "processed" / "order_forecasting.joblib"
METRICS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "forecasting_metrics.json"
)


def main() -> None:
    raw_frame = load_historical_orders(DATA_PATH)
    prepared_frame = build_training_frame(raw_frame)

    model, metrics = train_and_evaluate(prepared_frame)
    model.save(MODEL_PATH)

    metrics_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **metrics.to_dict(),
        **model_metadata(model),
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )

    print("Forecasting model training completed.")
    print(f"Model artifact: {MODEL_PATH}")
    print(f"Metrics file: {METRICS_PATH}")
    print(json.dumps(metrics_payload, indent=2))

    if metrics.mae > metrics.baseline_mae:
        raise SystemExit(
            "The trained model did not outperform the 24-hour seasonal baseline."
        )


if __name__ == "__main__":
    main()
