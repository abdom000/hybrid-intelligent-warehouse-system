from datetime import datetime, timezone

from hybrid_warehouse.assignment import (
    BASE_WEIGHTS,
    RobotRanker,
    build_replanning_result,
    resolve_weights,
)
from hybrid_warehouse.schemas import (
    DecisionType,
    FinalAssignmentDecision,
    ReplanningStatus,
    RobotFailureEvent,
    RobotRankingCandidate,
    RobotRankingInput,
)
from hybrid_warehouse.schemas.assignment import (
    ForecastSummary,
    RankingForecastSummary,
    RankingOrderSummary,
    ShelfSummary,
)


def ranking_input(candidates: list[RobotRankingCandidate]) -> RobotRankingInput:
    return RobotRankingInput(
        order=RankingOrderSummary(order_id="O1", priority="normal", total_weight_kg=10.0),
        forecast=RankingForecastSummary(expected_orders=24, load_level="low"),
        candidates=candidates,
        requested_at=datetime.now(timezone.utc),
    )


def candidate(
    robot_id: str,
    *,
    battery: float = 80.0,
    workload: int = 0,
    distance: float = 40.0,
) -> RobotRankingCandidate:
    return RobotRankingCandidate(
        robot_id=robot_id,
        battery_level=battery,
        current_workload=workload,
        distance_meters=distance,
        estimated_travel_seconds=distance * 0.85,
    )


def test_best_robot_wins_on_all_components():
    result = RobotRanker().rank(
        ranking_input(
            [
                candidate("R1", battery=82.5, workload=0, distance=45.0),
                candidate("R3", battery=70.0, workload=1, distance=55.0),
            ]
        )
    )
    assert result.assignment_possible
    assert result.selected_robot_id == "R1"
    assert [item.robot_id for item in result.ranked_candidates] == ["R1", "R3"]


def test_empty_candidate_list_makes_assignment_impossible():
    result = RobotRanker().rank(ranking_input([]))
    assert not result.assignment_possible
    assert result.selected_robot_id is None


def test_equal_candidates_tie_break_deterministically():
    result = RobotRanker().rank(
        ranking_input([candidate("R9"), candidate("R2")])
    )
    assert result.selected_robot_id == "R2"


def test_score_components_are_exposed():
    result = RobotRanker().rank(ranking_input([candidate("R1")]))
    components = result.ranked_candidates[0].score_components
    assert set(components) == {"battery", "workload", "distance"}


def test_prioritize_speed_constraint_boosts_distance_weight():
    weights = resolve_weights(["prioritize_speed"])
    assert weights["distance"] > BASE_WEIGHTS["distance"]
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_speed_constraint_can_change_the_winner():
    slow_but_charged = candidate("R1", battery=100.0, workload=0, distance=50.0)
    close_but_low = candidate("R2", battery=30.0, workload=2, distance=5.0)

    neutral = RobotRanker().rank(ranking_input([slow_but_charged, close_but_low]))
    urgent = RobotRanker().rank(
        ranking_input([slow_but_charged, close_but_low]),
        constraints=["prioritize_speed"],
    )
    assert neutral.selected_robot_id == "R1"
    assert urgent.selected_robot_id == "R2"


# -- replanning ---------------------------------------------------------------


def failure_event() -> RobotFailureEvent:
    return RobotFailureEvent(
        robot_id="R1",
        assignment_id="A-OLD",
        order_id="O101",
        previous_status="busy",
        new_status="failed",
        failure_reason="Motor failure.",
        detected_at=datetime.now(timezone.utc),
    )


def decision(decision_type: DecisionType) -> FinalAssignmentDecision:
    assigned = decision_type == DecisionType.ASSIGNED
    return FinalAssignmentDecision(
        decision_id="D-NEW",
        assignment_id="A-NEW" if assigned else None,
        order_id="O101",
        decision=decision_type,
        selected_robot_id="R3" if assigned else None,
        route=["ZONE-D", "ZONE-C", "ZONE-B"] if assigned else [],
        distance_meters=55.0 if assigned else None,
        forecast_summary=ForecastSummary(expected_orders=24, load_level="low"),
        shelf_summary=ShelfSummary(shelf_id="S1", status="normal", confidence=0.92),
        rejected_robots=[],
        explanation=["Re-evaluated after failure."],
        created_at=datetime.now(timezone.utc),
    )


def test_successful_replanning_reports_replacement():
    result = build_replanning_result(
        event=failure_event(), new_decision=decision(DecisionType.ASSIGNED)
    )
    assert result.status == ReplanningStatus.REASSIGNED
    assert result.replacement_robot_id == "R3"
    assert result.new_assignment_id == "A-NEW"
    assert result.previous_assignment_id == "A-OLD"


def test_failed_replanning_has_no_replacement():
    result = build_replanning_result(
        event=failure_event(), new_decision=decision(DecisionType.REJECTED)
    )
    assert result.status == ReplanningStatus.REASSIGNMENT_FAILED
    assert result.replacement_robot_id is None
    assert result.new_assignment_id is None
