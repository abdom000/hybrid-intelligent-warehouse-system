from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from hybrid_warehouse.expert_system import (
    MANUAL_REVIEW_REQUIRED,
    ORDER_REJECTED,
    InferenceOutcome,
)
from hybrid_warehouse.routing import RoutePlanner
from hybrid_warehouse.schemas import (
    DecisionType,
    ExpertSystemFacts,
    FinalAssignmentDecision,
    RobotRankingCandidate,
    RobotRankingInput,
    RobotRankingResult,
    RouteResult,
)
from hybrid_warehouse.schemas.assignment import (
    ForecastSummary,
    RankingForecastSummary,
    RankingOrderSummary,
    ShelfSummary,
)

from .ranking import RobotRanker

ORDER_REJECTED_REASON_PREFIX = "order_rejected_reason:"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


class AssignmentPipeline:
    """Combines expert-system output, route planning, and ranking into a
    final explainable assignment decision.

    Decision order:

    1. an ``order_rejected`` constraint rejects the order outright;
    2. a ``manual_review_required`` constraint delegates to a human;
    3. otherwise eligible robots are routed to the shelf zone, robots
       without an available route are dropped, and the remaining
       candidates are ranked to select one robot.
    """

    def __init__(self, route_planner: RoutePlanner) -> None:
        self.route_planner = route_planner
        self.ranker = RobotRanker()

    def decide(
        self,
        facts: ExpertSystemFacts,
        outcome: InferenceOutcome,
    ) -> tuple[FinalAssignmentDecision, RobotRankingResult | None]:
        result = outcome.result
        explanation = list(outcome.trace)
        rejected_robots: list[dict[str, Any]] = [
            rejected.model_dump(mode="json") for rejected in result.rejected_robots
        ]

        forecast_summary = ForecastSummary(
            expected_orders=facts.forecast.expected_orders,
            load_level=facts.forecast.load_level,
        )
        shelf_summary = ShelfSummary(
            shelf_id=facts.shelf.shelf_id,
            status=facts.shelf.status,
            confidence=facts.shelf.confidence,
        )

        def build(
            decision: DecisionType,
            *,
            assignment_id: str | None = None,
            selected_robot_id: str | None = None,
            route: RouteResult | None = None,
            final_note: str,
        ) -> FinalAssignmentDecision:
            explanation.append(final_note)
            return FinalAssignmentDecision(
                decision_id=_new_id("D"),
                assignment_id=assignment_id,
                order_id=facts.order.order_id,
                decision=decision,
                selected_robot_id=selected_robot_id,
                route=list(route.route) if route is not None else [],
                distance_meters=route.distance_meters if route is not None else None,
                forecast_summary=forecast_summary,
                shelf_summary=shelf_summary,
                rejected_robots=rejected_robots,
                explanation=explanation,
                created_at=datetime.now(timezone.utc),
            )

        if ORDER_REJECTED in result.decision_constraints:
            reasons = [
                constraint.removeprefix(ORDER_REJECTED_REASON_PREFIX)
                for constraint in result.decision_constraints
                if constraint.startswith(ORDER_REJECTED_REASON_PREFIX)
            ]
            note = "Final decision: order rejected. " + (
                " ".join(reasons) if reasons else "The expert system rejected the order."
            )
            return build(DecisionType.REJECTED, final_note=note), None

        if MANUAL_REVIEW_REQUIRED in result.decision_constraints:
            return (
                build(
                    DecisionType.MANUAL_REVIEW_REQUIRED,
                    final_note=(
                        "Final decision: manual review required. The shelf state "
                        "cannot be trusted automatically, so a human operator must "
                        "confirm it before any robot is dispatched."
                    ),
                ),
                None,
            )

        # Route planning for eligible robots.
        robots_by_id = {robot.robot_id: robot for robot in facts.robots}
        routes: dict[str, RouteResult] = {}
        candidates: list[RobotRankingCandidate] = []

        for robot_id in result.eligible_robot_ids:
            robot = robots_by_id[robot_id]
            route = self.route_planner.plan_route(
                robot_id=robot_id,
                start_zone_id=robot.current_zone_id,
                destination_zone_id=facts.shelf.zone_id,
            )
            if not route.route_available:
                rejected_robots.append(
                    {
                        "robot_id": robot_id,
                        "reasons": [
                            f"No available route from {robot.current_zone_id} "
                            f"to {facts.shelf.zone_id}."
                        ],
                        "applied_rules": ["ROUTING-NO-PATH"],
                    }
                )
                explanation.append(
                    f"Robot {robot_id} dropped: no available route from "
                    f"{robot.current_zone_id} to {facts.shelf.zone_id}."
                )
                continue
            routes[robot_id] = route
            candidates.append(
                RobotRankingCandidate(
                    robot_id=robot_id,
                    battery_level=robot.battery_level,
                    current_workload=robot.current_workload,
                    distance_meters=route.distance_meters,
                    estimated_travel_seconds=route.estimated_travel_seconds,
                )
            )
            explanation.append(
                f"Robot {robot_id} route planned: {' -> '.join(route.route)} "
                f"({route.distance_meters} m, ~{route.estimated_travel_seconds} s)."
            )

        ranking_input = RobotRankingInput(
            order=RankingOrderSummary(
                order_id=facts.order.order_id,
                priority=facts.order.priority,
                total_weight_kg=facts.order.total_weight_kg,
            ),
            forecast=RankingForecastSummary(
                expected_orders=facts.forecast.expected_orders,
                load_level=facts.forecast.load_level,
            ),
            candidates=candidates,
            requested_at=datetime.now(timezone.utc),
        )
        ranking = self.ranker.rank(
            ranking_input, constraints=result.decision_constraints
        )
        explanation.append(f"Ranking: {ranking.reason}")

        if not ranking.assignment_possible:
            return (
                build(
                    DecisionType.REJECTED,
                    final_note=(
                        "Final decision: order rejected. No suitable robot is "
                        "currently able to serve this order."
                    ),
                ),
                ranking,
            )

        selected_id = ranking.selected_robot_id
        assert selected_id is not None
        return (
            build(
                DecisionType.ASSIGNED,
                assignment_id=_new_id("A"),
                selected_robot_id=selected_id,
                route=routes[selected_id],
                final_note=(
                    f"Final decision: order {facts.order.order_id} assigned to "
                    f"robot {selected_id}."
                ),
            ),
            ranking,
        )
