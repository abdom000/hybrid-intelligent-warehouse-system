"""API tests for the FastAPI backend using the in-process test client."""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hybrid_warehouse.backend import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app(PROJECT_ROOT, database_path=":memory:")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def fresh_state(client):
    client.post("/api/reset")


def test_dashboard_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "HiveWare" in response.text


def test_state_endpoint_returns_all_sections(client):
    payload = client.get("/api/state").json()
    assert {"forecast", "robots", "orders", "rules"} <= set(payload)


def test_assign_endpoint_runs_the_full_pipeline(client):
    response = client.post("/api/orders/O101/assign")
    assert response.status_code == 200
    decision = response.json()
    assert decision["decision"] == "assigned"
    assert decision["selected_robot_id"] == "R1"
    assert decision["route"] == ["ZONE-A", "ZONE-C", "ZONE-B"]
    assert len(decision["explanation"]) >= 3


def test_assigning_twice_returns_conflict(client):
    assert client.post("/api/orders/O101/assign").status_code == 200
    response = client.post("/api/orders/O101/assign")
    assert response.status_code == 409
    assert response.json()["error_code"] == "orchestration_error"


def test_failure_endpoint_triggers_replanning(client):
    client.post("/api/orders/O101/assign")
    response = client.post("/api/robots/R1/fail")
    assert response.status_code == 200
    payload = response.json()
    assert payload["replanned"] is True
    assert payload["status"] == "reassigned"
    assert payload["replacement_robot_id"] == "R3"


def test_scenario_run_endpoint_reports_pass(client):
    response = client.post("/api/scenarios/SCENARIO-001/run")
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_rules_reload_endpoint(client):
    response = client.post("/api/rules/reload")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["loaded_rules"] >= 10


def test_invalid_rule_is_rejected_with_details(client):
    bad_rule = {"rule_id": "RULE-BROKEN"}
    response = client.post("/api/rules", json=bad_rule)
    assert response.status_code == 422


def test_unknown_order_returns_conflict(client):
    response = client.post("/api/orders/NOPE/assign")
    assert response.status_code == 409


# -- evolutionary knowledge-base extension over the API ------------------------


@pytest.fixture()
def sandbox_client(tmp_path) -> TestClient:
    """A client whose knowledge base lives in a temporary copy, so adding
    rules over the API does not modify the repository files."""
    shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
    app = create_app(tmp_path, database_path=":memory:")
    with TestClient(app) as test_client:
        yield test_client


def test_rule_added_at_runtime_changes_decisions(sandbox_client):
    # Baseline: O101 (urgent) is assigned to R1.
    baseline = sandbox_client.post("/api/orders/O101/assign").json()
    assert baseline["decision"] == "assigned"
    sandbox_client.post("/api/reset")

    # Add a stricter rule at runtime: urgent orders need 90% battery.
    new_rule = {
        "rule_id": "RULE-URGENT-MIN-BATTERY-90",
        "name": "Urgent orders need 90% battery",
        "description": "IF the order is urgent AND battery is below 90 THEN reject the robot.",
        "conditions": [
            {"field": "order.priority", "operator": "==", "value": "urgent"},
            {"field": "robot.battery_level", "operator": "<", "value": 90},
        ],
        "actions": [
            {"type": "reject_robot", "reason": "Urgent orders require at least 90% battery."}
        ],
        "priority": 60,
        "active": True,
        "version": "1.0.0",
    }
    response = sandbox_client.post("/api/rules", json=new_rule)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # The same order is now rejected: no robot satisfies the new rule
    # (R4 has 91% battery but is busy).
    decision = sandbox_client.post("/api/orders/O101/assign").json()
    assert decision["decision"] == "rejected"
    rejected_ids = {robot["robot_id"] for robot in decision["rejected_robots"]}
    assert "R1" in rejected_ids
