from datetime import datetime, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from hybrid_warehouse.schemas import (
    Order,
    OrderPriority,
    OrderStatus,
    Robot,
    RobotStatus,
    RouteResult,
    Shelf,
    ShelfStatus,
    AssignmentScenario,
    ReplanningScenario,
    Scenario,
)


def test_valid_robot() -> None:
    robot = Robot(
        robot_id="R1",
        current_zone_id="ZONE-A",
        battery_level=80,
        maximum_load_kg=50,
        current_load_kg=10,
        current_workload=0,
        status=RobotStatus.AVAILABLE,
        updated_at=datetime.now(timezone.utc),
    )

    assert robot.robot_id == "R1"


def test_robot_load_cannot_exceed_capacity() -> None:
    with pytest.raises(ValidationError):
        Robot(
            robot_id="R1",
            current_zone_id="ZONE-A",
            battery_level=80,
            maximum_load_kg=50,
            current_load_kg=60,
            current_workload=0,
            status=RobotStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )


def test_empty_shelf_requires_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        Shelf(
            shelf_id="S1",
            zone_id="ZONE-B",
            product_id="P1",
            status=ShelfStatus.EMPTY,
            available_quantity=5,
            last_updated_at=datetime.now(timezone.utc),
        )


def test_order_deadline_must_be_later_than_created_at() -> None:
    timestamp = datetime.now(timezone.utc)

    with pytest.raises(ValidationError):
        Order(
            order_id="O1",
            product_id="P1",
            shelf_id="S1",
            quantity=1,
            total_weight_kg=10,
            priority=OrderPriority.NORMAL,
            status=OrderStatus.PENDING,
            created_at=timestamp,
            deadline=timestamp,
        )


def test_route_must_end_at_destination() -> None:
    with pytest.raises(ValidationError):
        RouteResult(
            robot_id="R1",
            start_zone_id="ZONE-A",
            destination_zone_id="ZONE-B",
            route=["ZONE-A", "ZONE-C"],
            distance_meters=10,
            estimated_travel_seconds=8,
            route_available=True,
        )


def test_assignment_scenario_accepts_rejected_robot_ids() -> None:
    adapter = TypeAdapter(Scenario)
    scenario = adapter.validate_python(
        {
            "scenario_id": "SCENARIO-002",
            "name": "Battery rejection",
            "order_id": "O102",
            "expected_decision": "assigned",
            "expected_rejected_robot_ids": ["R2"],
            "notes": "R2 must be rejected.",
        }
    )

    assert isinstance(scenario, AssignmentScenario)
    assert scenario.expected_rejected_robot_ids == ["R2"]


def test_replanning_scenario_has_separate_shape() -> None:
    adapter = TypeAdapter(Scenario)
    scenario = adapter.validate_python(
        {
            "scenario_id": "SCENARIO-006",
            "name": "Robot failure and replanning",
            "order_id": "O101",
            "failed_robot_id": "R1",
            "expected_replacement_robot_id": "R3",
            "expected_status": "reassigned",
            "notes": "R3 is the replacement.",
        }
    )

    assert isinstance(scenario, ReplanningScenario)
    assert scenario.expected_replacement_robot_id == "R3"
