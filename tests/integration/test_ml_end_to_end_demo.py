from pathlib import Path

from hybrid_warehouse.integration import run_ml_end_to_end_demo


def test_ml_end_to_end_demo_builds_expert_system_facts() -> None:
    project_root = Path(__file__).resolve().parents[2]

    result = run_ml_end_to_end_demo(project_root)

    assert result["demo_status"] == "passed"
    assert result["order"]["order_id"] == "O101"
    assert result["forecast"]["expected_orders"] >= 0
    assert result["shelf_prediction"]["status"] == "unknown"
    assert result["shelf_prediction"]["requires_manual_review"] is True
    assert result["expert_system_facts"]["order"]["order_id"] == "O101"
    assert len(result["expert_system_facts"]["robots"]) == 5
