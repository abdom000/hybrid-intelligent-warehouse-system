from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.integration import run_ml_end_to_end_demo  # noqa: E402

REPORT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "ml_end_to_end_demo.json"
)


def main() -> None:
    payload = run_ml_end_to_end_demo(PROJECT_ROOT)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    facts = payload["expert_system_facts"]

    print("ML end-to-end demo passed.")
    print(f"Order: {facts['order']['order_id']}")
    print(f"Forecasted orders: {facts['forecast']['expected_orders']}")
    print(f"Forecast load: {facts['forecast']['load_level']}")
    print(f"Shelf status: {facts['shelf']['status']}")
    print(
        "Manual review required: "
        f"{facts['shelf']['requires_manual_review']}"
    )
    print(f"Robots passed to expert system: {len(facts['robots'])}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
