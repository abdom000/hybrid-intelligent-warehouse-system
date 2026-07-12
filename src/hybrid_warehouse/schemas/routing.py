from __future__ import annotations

from pydantic import Field, model_validator

from .common import WarehouseBaseModel


class RouteResult(WarehouseBaseModel):
    robot_id: str = Field(min_length=1)
    start_zone_id: str = Field(min_length=1)
    destination_zone_id: str = Field(min_length=1)
    route: list[str]
    distance_meters: float = Field(ge=0)
    estimated_travel_seconds: float = Field(ge=0)
    route_available: bool

    @model_validator(mode="after")
    def route_must_match_availability(self) -> "RouteResult":
        if self.route_available:
            if not self.route:
                raise ValueError("route must not be empty when route_available is true.")
            if self.route[0] != self.start_zone_id:
                raise ValueError("route must begin with start_zone_id.")
            if self.route[-1] != self.destination_zone_id:
                raise ValueError("route must end with destination_zone_id.")
        elif self.route:
            raise ValueError("route must be empty when route_available is false.")
        return self
