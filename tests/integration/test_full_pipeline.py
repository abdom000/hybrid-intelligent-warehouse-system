"""End-to-end tests for the full hybrid decision pipeline.

The orchestrator runs the complete chain on deterministic mock data:
forecasting + simulated shelf recognition -> ML integration ->
mivar expert system -> routing -> ranking -> final decision -> persistence.
Every documented scenario from data/mock/scenarios.json must reproduce
its expected outcome.
"""

from pathlib import Path

import pytest

from hybrid_warehouse.backend import OrchestrationError, WarehouseOrchestrator
from hybrid_warehouse.schemas import DecisionType

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def orchestrator() -> WarehouseOrchestrator:
    return WarehouseOrchestrator(PROJECT_ROOT, database_path=":memory:")


SCENARIO_IDS = [
    "SCENARIO-001",
    "SCENARIO-002",
    "SCENARIO-003",
    "SCENARIO-004",
    "SCENARIO-005",
    "SCENARIO-006",
]


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_documented_scenario_reproduces_expected_outcome(orchestrator, scenario_id):
    result = orchestrator.run_scenario(scenario_id)
    assert result["passed"], (
        f"{scenario_id} diverged from the documented expectation: "
        f"{result['actual']!r} (expected: {result['scenario']!r})"
    )


def test_assignment_mutates_order_and_robot_state(orchestrator):
    orchestrator.reset()
    decision = orchestrator.assign_order("O101")
    assert decision.decision == DecisionType.ASSIGNED
    assert decision.selected_robot_id == "R1"
    assert decision.route == ["ZONE-A", "ZONE-C", "ZONE-B"]

    assert str(orchestrator.orders["O101"].status) == "assigned"
    robot = orchestrator.robots["R1"]
    assert str(robot.status) == "busy"
    assert robot.current_workload == 1


def test_decisions_are_persisted_with_explanations(orchestrator):
    orchestrator.reset()
    orchestrator.assign_order("O101")
    decisions = orchestrator.repository.list_decisions()
    assert len(decisions) == 1
    assert len(decisions[0]["explanation"]) >= 3
    assert decisions[0]["decision"] == "assigned"


def test_replanning_after_failure_selects_next_best_robot(orchestrator):
    orchestrator.reset()
    orchestrator.assign_order("O101")
    replanning = orchestrator.fail_robot("R1")
    assert replanning is not None
    assert str(replanning.status) == "reassigned"
    assert replanning.replacement_robot_id == "R3"
    assert str(orchestrator.robots["R1"].status) == "failed"
    assert str(orchestrator.robots["R3"].status) == "busy"


def test_failing_idle_robot_needs_no_replanning(orchestrator):
    orchestrator.reset()
    assert orchestrator.fail_robot("R3") is None
    assert str(orchestrator.robots["R3"].status) == "failed"


def test_double_assignment_is_rejected(orchestrator):
    orchestrator.reset()
    orchestrator.assign_order("O101")
    with pytest.raises(OrchestrationError, match="not pending"):
        orchestrator.assign_order("O101")


def test_unknown_order_raises(orchestrator):
    with pytest.raises(OrchestrationError, match="Order not found"):
        orchestrator.assign_order("O999")


def test_state_snapshot_contains_all_dashboard_sections(orchestrator):
    orchestrator.reset()
    state = orchestrator.get_state()
    for key in (
        "forecast",
        "zones",
        "paths",
        "robots",
        "shelves",
        "orders",
        "decisions",
        "replannings",
        "rules",
        "vso_model",
        "active_assignments",
    ):
        assert key in state, f"missing state section: {key}"
    assert state["forecast"]["expected_orders"] >= 0
    assert len(state["rules"]) >= 10


def test_manual_review_keeps_order_pending(orchestrator):
    orchestrator.reset()
    decision = orchestrator.assign_order("O105")
    assert decision.decision == DecisionType.MANUAL_REVIEW_REQUIRED
    assert str(orchestrator.orders["O105"].status) == "pending"
