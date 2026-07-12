from enum import StrEnum


class OrderPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OrderStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RobotStatus(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    CHARGING = "charging"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


class ShelfStatus(StrEnum):
    EMPTY = "empty"
    LOW_STOCK = "low_stock"
    NORMAL = "normal"
    FULL = "full"
    UNKNOWN = "unknown"


class LoadLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionType(StrEnum):
    ASSIGNED = "assigned"
    REJECTED = "rejected"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class ReplanningStatus(StrEnum):
    REASSIGNED = "reassigned"
    REASSIGNMENT_FAILED = "reassignment_failed"
