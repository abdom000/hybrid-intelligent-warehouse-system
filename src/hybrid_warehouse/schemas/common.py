from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WarehouseBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
        protected_namespaces=(),
    )


class ErrorDetails(WarehouseBaseModel):
    field: str | None = None
    reason: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(WarehouseBaseModel):
    error_code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: ErrorDetails | dict[str, Any] | None = None
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_have_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include timezone information.")
        return value
