from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "forecasting_metrics.json"
)


def main() -> None:
    if not METRICS_PATH.exists():
        raise FileNotFoundError(
            "Forecasting metrics are missing. "
            "Run scripts/train_forecasting_model.py first."
        )

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    print("Forecasting evaluation summary")
    print(f"MAE: {metrics['mae']}")
    print(f"RMSE: {metrics['rmse']}")
    print(f"R2: {metrics['r2']}")
    print(f"Baseline MAE: {metrics['baseline_mae']}")
    print(
        "Improvement over baseline: "
        f"{metrics['improvement_over_baseline_percent']}%"
    )

    if metrics["mae"] > metrics["baseline_mae"]:
        raise SystemExit("Forecasting model is worse than the baseline.")


if __name__ == "__main__":
    main()
