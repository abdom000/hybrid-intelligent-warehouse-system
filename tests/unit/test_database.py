from datetime import datetime, timezone

import pytest

from hybrid_warehouse.database import WarehouseRepository
from hybrid_warehouse.schemas import (
    DecisionType,
    FinalAssignmentDecision,
    ReplanningResult,
    ReplanningStatus,
)
from hybrid_warehouse.schemas.assignment import ForecastSummary, ShelfSummary


@pytest.fixture()
def repository() -> WarehouseRepository:
    return WarehouseRepository(":memory:")


def assigned_decision(decision_id: str = "D-1") -> FinalAssignmentDecision:
    return FinalAssignmentDecision(
        decision_id=decision_id,
        assignment_id=f"A-{decision_id}",
        order_id="O101",
        decision=DecisionType.ASSIGNED,
        selected_robot_id="R1",
        route=["ZONE-A", "ZONE-C", "ZONE-B"],
        distance_meters=45.0,
        forecast_summary=ForecastSummary(expected_orders=24, load_level="low"),
        shelf_summary=ShelfSummary(shelf_id="S1", status="normal", confidence=0.92),
        rejected_robots=[{"robot_id": "R2", "reasons": ["low battery"]}],
        explanation=["step 1", "step 2"],
        created_at=datetime.now(timezone.utc),
    )


def test_decision_round_trip(repository):
    repository.save_decision(assigned_decision())
    stored = repository.get_decision("D-1")
    assert stored is not None
    assert stored["order_id"] == "O101"
    assert stored["explanation"] == ["step 1", "step 2"]
    assert repository.list_decisions()[0]["decision_id"] == "D-1"


def test_assigned_decision_creates_active_assignment(repository):
    repository.save_decision(assigned_decision())
    assignment = repository.get_active_assignment_for_robot("R1")
    assert assignment is not None
    assert assignment["order_id"] == "O101"
    assert assignment["route"] == ["ZONE-A", "ZONE-C", "ZONE-B"]


def test_assignment_status_update(repository):
    repository.save_decision(assigned_decision())
    repository.update_assignment_status("A-D-1", "failed")
    assert repository.get_active_assignment_for_robot("R1") is None
    assert repository.list_assignments(status="failed")


def test_archive_active_assignments(repository):
    repository.save_decision(assigned_decision())
    repository.archive_active_assignments()
    assert repository.get_active_assignment_for_robot("R1") is None
    assert repository.list_assignments(status="archived")


def test_replanning_round_trip(repository):
    result = ReplanningResult(
        previous_assignment_id="A-D-1",
        new_assignment_id="A-D-2",
        order_id="O101",
        failed_robot_id="R1",
        replacement_robot_id="R3",
        status=ReplanningStatus.REASSIGNED,
        explanation=["robot failed", "reassigned"],
        replanned_at=datetime.now(timezone.utc),
    )
    repository.save_replanning(result)
    stored = repository.list_replannings()
    assert stored[0]["replacement_robot_id"] == "R3"


def test_clear_all_removes_history(repository):
    repository.save_decision(assigned_decision())
    repository.clear_all()
    assert repository.list_decisions() == []
    assert repository.list_assignments() == []
