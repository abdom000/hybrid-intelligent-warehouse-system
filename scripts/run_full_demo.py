"""Run the complete hybrid decision pipeline in the console.

Executes every documented scenario from data/mock/scenarios.json through
the full chain (forecasting + simulated shelf recognition -> ML integration
-> mivar expert system -> routing -> ranking -> decision -> persistence)
and writes a JSON report to data/processed/full_system_demo.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.backend import WarehouseOrchestrator  # noqa: E402

REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "full_system_demo.json"


def main() -> int:
    print("Training the forecasting model and loading the knowledge base...")
    orchestrator = WarehouseOrchestrator(PROJECT_ROOT, database_path=":memory:")
    forecast = orchestrator.forecast
    print(
        f"Forecast: {forecast.expected_orders} orders expected next hour "
        f"(load level: {forecast.load_level}).\n"
    )

    results = []
    all_passed = True
    for scenario in orchestrator.load_scenarios():
        scenario_id = scenario["scenario_id"]
        result = orchestrator.run_scenario(scenario_id)
        results.append(result)
        all_passed = all_passed and result["passed"]

        verdict = "PASSED" if result["passed"] else "DIFFERS"
        print(f"[{verdict}] {scenario_id}: {scenario['name']}")
        print(f"         expected: {scenario.get('expected_decision') or scenario.get('expected_status')}")
        print(f"         actual:   {result['actual']}")

        explanation = (
            result.get("replanning") or result.get("decision") or {}
        ).get("explanation", [])
        for step in explanation:
            print(f"           - {step}")
        print()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "demo_status": "passed" if all_passed else "failed",
                "forecast": forecast.model_dump(mode="json"),
                "scenarios": results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Report: {REPORT_PATH}")
    if not all_passed:
        print("Some scenarios diverged from the documented expectations.")
        return 1
    print("All documented scenarios reproduced their expected outcomes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
