from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from .common import WarehouseBaseModel


class OrderFacts(WarehouseBaseModel):
    order_id: str = Field(min_length=1)
    priority: str = Field(min_length=1)
    total_weight_kg: float = Field(gt=0)
    shelf_id: str = Field(min_length=1)


class RobotFacts(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    battery_level: float = Field(ge=0, le=100)
    maximum_load_kg: float = Field(gt=0)
    current_zone_id: str = Field(min_length=1)
    current_workload: int = Field(ge=0)
    status: str = Field(min_length=1)


class ShelfFacts(WarehouseBaseModel):
    shelf_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    requires_manual_review: bool


class ForecastFacts(WarehouseBaseModel):
    expected_orders: int = Field(ge=0)
    load_level: str = Field(min_length=1)


class ExpertSystemFacts(WarehouseBaseModel):
    order: OrderFacts
    robots: list[RobotFacts]
    shelf: ShelfFacts
    forecast: ForecastFacts
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must include timezone information.")
        return value


class RejectedRobot(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    reasons: list[str] = Field(min_length=1)
    applied_rules: list[str] = Field(default_factory=list)


class ExpertSystemResult(WarehouseBaseModel):
    order_id: str = Field(min_length=1)
    eligible_robot_ids: list[str]
    rejected_robots: list[RejectedRobot]
    applied_rules: list[str]
    decision_constraints: list[str]
    evaluated_at: datetime

    @field_validator("evaluated_at")
    @classmethod
    def evaluated_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("evaluated_at must include timezone information.")
        return value


class RuleCondition(WarehouseBaseModel):
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: Any


class RuleAction(WarehouseBaseModel):
    type: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Rule(WarehouseBaseModel):
    rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    conditions: list[RuleCondition] = Field(min_length=1)
    actions: list[RuleAction] = Field(min_length=1)
    priority: int = Field(ge=0)
    active: bool
    version: str = Field(min_length=1)


class RuleReloadResult(WarehouseBaseModel):
    success: bool
    loaded_rules: int = Field(ge=0)
    rejected_rules: int = Field(ge=0)
    errors: list[dict[str, Any]]
    reloaded_at: datetime

    @field_validator("reloaded_at")
    @classmethod
    def reloaded_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reloaded_at must include timezone information.")
        return value
