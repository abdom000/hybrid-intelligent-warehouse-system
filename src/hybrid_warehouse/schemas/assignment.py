from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator, model_validator

from .common import WarehouseBaseModel
from .enums import DecisionType, ReplanningStatus


class RankingOrderSummary(WarehouseBaseModel):
    order_id: str = Field(min_length=1)
    priority: str = Field(min_length=1)
    total_weight_kg: float = Field(gt=0)


class RankingForecastSummary(WarehouseBaseModel):
    expected_orders: int = Field(ge=0)
    load_level: str = Field(min_length=1)


class RobotRankingCandidate(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    battery_level: float = Field(ge=0, le=100)
    current_workload: int = Field(ge=0)
    distance_meters: float = Field(ge=0)
    estimated_travel_seconds: float = Field(ge=0)


class RobotRankingInput(WarehouseBaseModel):
    order: RankingOrderSummary
    forecast: RankingForecastSummary
    candidates: list[RobotRankingCandidate]
    requested_at: datetime

    @field_validator("requested_at")
    @classmethod
    def requested_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("requested_at must include timezone information.")
        return value


class RankedCandidate(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    score: float
    score_components: dict[str, float]


class RobotRankingResult(WarehouseBaseModel):
    order_id: str = Field(min_length=1)
    selected_robot_id: str | None
    ranked_candidates: list[RankedCandidate]
    assignment_possible: bool
    reason: str = Field(min_length=1)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must include timezone information.")
        return value

    @model_validator(mode="after")
    def selected_robot_must_match_assignment_state(self) -> "RobotRankingResult":
        if self.assignment_possible and self.selected_robot_id is None:
            raise ValueError(
                "selected_robot_id is required when assignment_possible is true."
            )
        if not self.assignment_possible and self.selected_robot_id is not None:
            raise ValueError(
                "selected_robot_id must be null when assignment_possible is false."
            )
        return self


class ForecastSummary(WarehouseBaseModel):
    expected_orders: int = Field(ge=0)
    load_level: str = Field(min_length=1)


class ShelfSummary(WarehouseBaseModel):
    shelf_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class FinalAssignmentDecision(WarehouseBaseModel):
    decision_id: str = Field(min_length=1)
    assignment_id: str | None
    order_id: str = Field(min_length=1)
    decision: DecisionType
    selected_robot_id: str | None
    route: list[str]
    distance_meters: float | None = Field(default=None, ge=0)
    forecast_summary: ForecastSummary
    shelf_summary: ShelfSummary
    rejected_robots: list[dict[str, Any]]
    explanation: list[str] = Field(min_length=1)
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def created_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must include timezone information.")
        return value

    @model_validator(mode="after")
    def assigned_decision_requires_assignment_data(self) -> "FinalAssignmentDecision":
        if self.decision == DecisionType.ASSIGNED:
            if self.assignment_id is None or self.selected_robot_id is None:
                raise ValueError(
                    "Assigned decisions require assignment_id and selected_robot_id."
                )
            if not self.route:
                raise ValueError("Assigned decisions require a non-empty route.")
        else:
            if self.assignment_id is not None or self.selected_robot_id is not None:
                raise ValueError(
                    "Non-assigned decisions must not contain assignment or robot IDs."
                )
        return self


class RobotFailureEvent(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    assignment_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    previous_status: str = Field(min_length=1)
    new_status: str = Field(pattern="^failed$")
    failure_reason: str = Field(min_length=1)
    detected_at: datetime

    @field_validator("detected_at")
    @classmethod
    def detected_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("detected_at must include timezone information.")
        return value


class ReplanningResult(WarehouseBaseModel):
    previous_assignment_id: str = Field(min_length=1)
    new_assignment_id: str | None
    order_id: str = Field(min_length=1)
    failed_robot_id: str = Field(min_length=1)
    replacement_robot_id: str | None
    status: ReplanningStatus
    explanation: list[str] = Field(min_length=1)
    replanned_at: datetime

    @field_validator("replanned_at")
    @classmethod
    def replanned_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("replanned_at must include timezone information.")
        return value

    @model_validator(mode="after")
    def replacement_data_must_match_status(self) -> "ReplanningResult":
        if self.status == ReplanningStatus.REASSIGNED:
            if self.new_assignment_id is None or self.replacement_robot_id is None:
                raise ValueError(
                    "Reassigned results require new assignment and replacement robot."
                )
        else:
            if self.new_assignment_id is not None or self.replacement_robot_id is not None:
                raise ValueError(
                    "Failed replanning must not contain replacement assignment data."
                )
        return self
