from __future__ import annotations

from datetime import datetime, timezone

from hybrid_warehouse.schemas import (
    RankedCandidate,
    RobotRankingInput,
    RobotRankingResult,
)

BASE_WEIGHTS = {
    "battery": 0.35,
    "workload": 0.25,
    "distance": 0.40,
}

# Constraints emitted by the expert system shift the ranking focus.
CONSTRAINT_WEIGHT_BOOSTS = {
    "prioritize_speed": ("distance", 0.20),
    "prefer_low_workload": ("workload", 0.20),
}

# Robots with current_workload >= 3 are rejected by the expert system,
# so 3 is the effective workload ceiling for normalization.
WORKLOAD_CEILING = 3


def resolve_weights(constraints: list[str]) -> dict[str, float]:
    weights = dict(BASE_WEIGHTS)
    for constraint in constraints:
        boost = CONSTRAINT_WEIGHT_BOOSTS.get(constraint)
        if boost is not None:
            component, amount = boost
            weights[component] += amount
    total = sum(weights.values())
    return {component: value / total for component, value in weights.items()}


class RobotRanker:
    """Deterministic multi-criteria ranking of eligible robots.

    Each candidate receives a weighted score built from three normalized
    components: battery level, inverse workload, and inverse travel
    distance. Expert-system constraints (for example ``prioritize_speed``
    for urgent orders) increase the weight of the matching component, so
    the logical layer directly steers the numeric ranking.
    """

    def rank(
        self,
        ranking_input: RobotRankingInput,
        *,
        constraints: list[str] | None = None,
    ) -> RobotRankingResult:
        constraints = constraints or []
        weights = resolve_weights(constraints)

        if not ranking_input.candidates:
            return RobotRankingResult(
                order_id=ranking_input.order.order_id,
                selected_robot_id=None,
                ranked_candidates=[],
                assignment_possible=False,
                reason="No candidate robots remained after rule filtering and route planning.",
                generated_at=datetime.now(timezone.utc),
            )

        max_distance = max(
            candidate.distance_meters for candidate in ranking_input.candidates
        )

        ranked: list[RankedCandidate] = []
        for candidate in ranking_input.candidates:
            battery_score = candidate.battery_level / 100.0
            workload_score = 1.0 - min(
                candidate.current_workload, WORKLOAD_CEILING
            ) / WORKLOAD_CEILING
            distance_score = (
                1.0 - candidate.distance_meters / max_distance
                if max_distance > 0
                else 1.0
            )

            components = {
                "battery": round(weights["battery"] * battery_score, 4),
                "workload": round(weights["workload"] * workload_score, 4),
                "distance": round(weights["distance"] * distance_score, 4),
            }
            ranked.append(
                RankedCandidate(
                    robot_id=candidate.robot_id,
                    score=round(sum(components.values()), 4),
                    score_components=components,
                )
            )

        ranked.sort(key=lambda candidate: (-candidate.score, candidate.robot_id))
        selected = ranked[0]

        reason = (
            f"Robot {selected.robot_id} has the highest weighted score "
            f"{selected.score:.4f} (weights: battery {weights['battery']:.2f}, "
            f"workload {weights['workload']:.2f}, distance {weights['distance']:.2f}"
            f"{'; constraints: ' + ', '.join(constraints) if constraints else ''})."
        )

        return RobotRankingResult(
            order_id=ranking_input.order.order_id,
            selected_robot_id=selected.robot_id,
            ranked_candidates=ranked,
            assignment_possible=True,
            reason=reason,
            generated_at=datetime.now(timezone.utc),
        )
