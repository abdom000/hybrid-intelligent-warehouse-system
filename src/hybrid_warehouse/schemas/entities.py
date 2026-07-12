from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from .common import WarehouseBaseModel
from .enums import OrderPriority, OrderStatus, RobotStatus, ShelfStatus


class Product(WarehouseBaseModel):
    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit_weight_kg: float = Field(gt=0)
    active: bool


class WarehouseZone(WarehouseBaseModel):
    zone_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    active: bool


class WarehousePath(WarehouseBaseModel):
    path_id: str = Field(min_length=1)
    start_zone_id: str = Field(min_length=1)
    end_zone_id: str = Field(min_length=1)
    distance_meters: float = Field(gt=0)
    estimated_travel_seconds: float = Field(gt=0)
    active: bool

    @model_validator(mode="after")
    def zones_must_be_different(self) -> "WarehousePath":
        if self.start_zone_id == self.end_zone_id:
            raise ValueError("start_zone_id and end_zone_id must be different.")
        return self


class Shelf(WarehouseBaseModel):
    shelf_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    status: ShelfStatus
    available_quantity: int = Field(ge=0)
    last_updated_at: datetime

    @field_validator("last_updated_at")
    @classmethod
    def last_updated_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("last_updated_at must include timezone information.")
        return value

    @model_validator(mode="after")
    def empty_shelf_must_have_zero_quantity(self) -> "Shelf":
        if self.status == ShelfStatus.EMPTY and self.available_quantity != 0:
            raise ValueError("An empty shelf must have available_quantity equal to 0.")
        return self


class Robot(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    current_zone_id: str = Field(min_length=1)
    battery_level: float = Field(ge=0, le=100)
    maximum_load_kg: float = Field(gt=0)
    current_load_kg: float = Field(ge=0)
    current_workload: int = Field(ge=0)
    status: RobotStatus
    updated_at: datetime

    @field_validator("updated_at")
    @classmethod
    def updated_at_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("updated_at must include timezone information.")
        return value

    @model_validator(mode="after")
    def current_load_must_fit_capacity(self) -> "Robot":
        if self.current_load_kg > self.maximum_load_kg:
            raise ValueError("current_load_kg must not exceed maximum_load_kg.")
        return self


class Order(WarehouseBaseModel):
    order_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    shelf_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    total_weight_kg: float = Field(gt=0)
    priority: OrderPriority
    status: OrderStatus
    created_at: datetime
    deadline: datetime | None = None

    @field_validator("created_at", "deadline")
    @classmethod
    def datetime_must_have_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("datetime values must include timezone information.")
        return value

    @model_validator(mode="after")
    def deadline_must_follow_creation(self) -> "Order":
        if self.deadline is not None and self.deadline <= self.created_at:
            raise ValueError("deadline must be later than created_at.")
        return self


class AssignmentScenario(WarehouseBaseModel):
    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    expected_decision: str = Field(min_length=1)
    expected_selected_robot_id: str | None = None
    expected_rejected_robot_ids: list[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class ReplanningScenario(WarehouseBaseModel):
    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    failed_robot_id: str = Field(min_length=1)
    expected_replacement_robot_id: str = Field(min_length=1)
    expected_status: str = Field(min_length=1)
    notes: str = Field(min_length=1)


Scenario = AssignmentScenario | ReplanningScenario

class ShelfImageManifestItem(WarehouseBaseModel):
    image_id: str = Field(min_length=1)
    shelf_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    expected_status: ShelfStatus
    available: bool


class HistoricalOrderRecord(WarehouseBaseModel):
    timestamp: datetime
    order_count: int = Field(ge=0)
    hour: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)
    is_weekend: bool

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information.")
        return value
