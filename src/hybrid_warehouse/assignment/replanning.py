from __future__ import annotations

from datetime import datetime, timezone

from hybrid_warehouse.schemas import (
    DecisionType,
    FinalAssignmentDecision,
    ReplanningResult,
    ReplanningStatus,
    RobotFailureEvent,
)


def build_replanning_result(
    *,
    event: RobotFailureEvent,
    new_decision: FinalAssignmentDecision,
) -> ReplanningResult:
    """Convert a failure event plus a re-run assignment decision into a
    replanning result.

    The caller marks the robot as failed and re-runs the normal assignment
    pipeline; this function only interprets the outcome, so replanning
    reuses exactly the same rules, routing, and ranking as the original
    assignment.
    """
    explanation = [
        f"Robot {event.robot_id} failed while executing assignment "
        f"{event.assignment_id}: {event.failure_reason}",
        f"Order {event.order_id} was returned to the queue and the assignment "
        "pipeline was re-run without the failed robot.",
        *new_decision.explanation,
    ]

    if new_decision.decision == DecisionType.ASSIGNED:
        return ReplanningResult(
            previous_assignment_id=event.assignment_id,
            new_assignment_id=new_decision.assignment_id,
            order_id=event.order_id,
            failed_robot_id=event.robot_id,
            replacement_robot_id=new_decision.selected_robot_id,
            status=ReplanningStatus.REASSIGNED,
            explanation=explanation,
            replanned_at=datetime.now(timezone.utc),
        )

    explanation.append(
        "No replacement robot could be selected; the order requires operator attention."
    )
    return ReplanningResult(
        previous_assignment_id=event.assignment_id,
        new_assignment_id=None,
        order_id=event.order_id,
        failed_robot_id=event.robot_id,
        replacement_robot_id=None,
        status=ReplanningStatus.REASSIGNMENT_FAILED,
        explanation=explanation,
        replanned_at=datetime.now(timezone.utc),
    )
