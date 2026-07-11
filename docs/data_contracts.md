# Data Contracts

## Document Information

| Field | Value |
|---|---|
| Project name | Hybrid Intelligent Warehouse System |
| Document version | 0.1 |
| Document type | Module Data Contracts |
| Team | Abdelrahman and Halit |
| Current phase | Interface design |

## 1. Purpose

This document defines the structured data exchanged between the modules of the Hybrid Intelligent Warehouse System.

The contracts ensure that:

- module inputs and outputs are predictable;
- field names remain consistent;
- data types are validated;
- integration can begin before all modules are fully implemented;
- mock outputs can replace unavailable models during development;
- backend, machine-learning, and expert-system modules can be developed independently.

All timestamps must use ISO 8601 format in UTC.

Example:

```text
2026-07-01T14:00:00Z
```

All identifiers must be non-empty strings.

Examples:

```text
O101
R1
S7
P15
ZONE-A
```

## 2. Common Conventions

### 2.1 Identifier Convention

Identifiers should use the following prefixes:

| Entity | Prefix | Example |
|---|---|---|
| Order | `O` | `O101` |
| Robot | `R` | `R1` |
| Shelf | `S` | `S7` |
| Product | `P` | `P15` |
| Zone | `ZONE-` | `ZONE-A` |
| Assignment | `A` | `A501` |
| Decision | `D` | `D9001` |
| Rule | `RULE-` | `RULE-001` |

### 2.2 Numeric Conventions

- battery values are represented as percentages from `0` to `100`;
- confidence values are represented from `0.0` to `1.0`;
- weight values are represented in kilograms;
- distance values are represented in meters;
- duration values are represented in seconds or minutes;
- scores are numeric values where a higher score means a better candidate.

### 2.3 Standard Error Contract

All modules must return errors using the following structure:

| Field | Type | Required | Description |
|---|---|---:|---|
| `error_code` | string | Yes | Machine-readable error identifier |
| `message` | string | Yes | Human-readable error message |
| `details` | object | No | Additional structured error information |
| `timestamp` | string | Yes | Error-generation time |

Example:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "The request contains invalid data.",
  "details": {
    "field": "battery_level",
    "reason": "Value must be between 0 and 100."
  },
  "timestamp": "2026-07-01T13:55:00Z"
}
```

## 3. Forecast Result Contract

The Forecasting module returns the expected warehouse workload for the next hour.

### 3.1 Producer

```text
Order Forecasting Module
```

Owner:

```text
Abdelrahman
```

### 3.2 Consumers

```text
Integration and Orchestration Module
Database Access Module
```

The Orchestration module converts the result into facts before sending relevant values to the Expert System.

### 3.3 Output Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `forecast_time` | string | Yes | Start time of the predicted interval |
| `forecast_horizon_minutes` | integer | Yes | Forecast duration in minutes |
| `expected_orders` | integer | Yes | Predicted number of orders |
| `load_level` | string | Yes | Classified warehouse workload |
| `model_version` | string | Yes | Version of the forecasting model |
| `generated_at` | string | Yes | Time when the prediction was generated |

### 3.4 Allowed Values

The `load_level` field must contain one of:

```text
low
medium
high
```

The initial forecast horizon must be:

```text
60 minutes
```

### 3.5 Validation Rules

1. `forecast_time` must be a valid ISO 8601 timestamp;
2. `forecast_horizon_minutes` must be greater than zero;
3. `expected_orders` must be zero or greater;
4. `load_level` must contain a supported value;
5. `model_version` must not be empty;
6. `generated_at` must be a valid ISO 8601 timestamp.

### 3.6 Example Output

```json
{
  "forecast_time": "2026-07-01T14:00:00Z",
  "forecast_horizon_minutes": 60,
  "expected_orders": 180,
  "load_level": "high",
  "model_version": "forecast-v0.1",
  "generated_at": "2026-07-01T13:55:00Z"
}
```

### 3.7 Failure Output

```json
{
  "error_code": "FORECAST_UNAVAILABLE",
  "message": "The forecasting model could not generate a prediction.",
  "details": {
    "reason": "Model artifact was not found."
  },
  "timestamp": "2026-07-01T13:55:00Z"
}
```

### 3.8 Mock Output

```json
{
  "forecast_time": "2026-07-01T14:00:00Z",
  "forecast_horizon_minutes": 60,
  "expected_orders": 120,
  "load_level": "medium",
  "model_version": "mock-v0.1",
  "generated_at": "2026-07-01T13:55:00Z"
}
```

## 4. Shelf Recognition Result Contract

The Shelf Recognition module returns the predicted condition of a warehouse shelf.

### 4.1 Producer

```text
Shelf Recognition Module
```

Owner:

```text
Abdelrahman
```

### 4.2 Consumers

```text
Integration and Orchestration Module
Database Access Module
```

The Orchestration module converts the result into facts before sending relevant values to the Expert System.

### 4.3 Output Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `shelf_id` | string | Yes | Unique shelf identifier |
| `status` | string | Yes | Predicted shelf condition |
| `confidence` | number | Yes | Prediction confidence between 0 and 1 |
| `model_version` | string | Yes | Version of the image-classification model |
| `prediction_time` | string | Yes | Time when the prediction was generated |
| `requires_manual_review` | boolean | Yes | Indicates whether human inspection is required |

### 4.4 Allowed Values

The `status` field must contain one of:

```text
empty
low_stock
normal
full
unknown
```

### 4.5 Validation Rules

1. `shelf_id` must not be empty;
2. `status` must contain a supported value;
3. `confidence` must be between 0 and 1;
4. `model_version` must not be empty;
5. `prediction_time` must be a valid ISO 8601 timestamp;
6. `requires_manual_review` must be `true` when confidence is below the configured threshold.

The initial confidence threshold is:

```text
0.60
```

### 4.6 Example Output

```json
{
  "shelf_id": "S7",
  "status": "low_stock",
  "confidence": 0.91,
  "model_version": "shelf-v0.1",
  "prediction_time": "2026-07-01T13:55:00Z",
  "requires_manual_review": false
}
```

### 4.7 Low-Confidence Example

```json
{
  "shelf_id": "S7",
  "status": "unknown",
  "confidence": 0.42,
  "model_version": "shelf-v0.1",
  "prediction_time": "2026-07-01T13:55:00Z",
  "requires_manual_review": true
}
```

### 4.8 Failure Output

```json
{
  "error_code": "SHELF_PREDICTION_FAILED",
  "message": "The shelf image could not be processed.",
  "details": {
    "reason": "Unsupported image format."
  },
  "timestamp": "2026-07-01T13:55:00Z"
}
```

### 4.9 Mock Output

```json
{
  "shelf_id": "S7",
  "status": "normal",
  "confidence": 0.88,
  "model_version": "mock-v0.1",
  "prediction_time": "2026-07-01T13:55:00Z",
  "requires_manual_review": false
}
```

## 5. Order Contract

The Order contract represents a warehouse order that requires robot execution.

### 5.1 Producer

```text
Backend API
Database Access Module
```

### 5.2 Consumers

```text
Integration and Orchestration Module
Expert System Module
Robot Assignment Module
```

### 5.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `order_id` | string | Yes | Unique order identifier |
| `product_id` | string | Yes | Required product identifier |
| `shelf_id` | string | Yes | Shelf containing the product |
| `quantity` | integer | Yes | Required product quantity |
| `total_weight_kg` | number | Yes | Total order weight |
| `priority` | string | Yes | Order priority |
| `status` | string | Yes | Current order status |
| `created_at` | string | Yes | Order creation time |
| `deadline` | string | No | Optional required completion time |

### 5.4 Allowed Priority Values

```text
low
normal
high
urgent
```

### 5.5 Allowed Status Values

```text
pending
assigned
in_progress
completed
rejected
cancelled
```

### 5.6 Validation Rules

1. `order_id` must not be empty;
2. `product_id` must not be empty;
3. `shelf_id` must not be empty;
4. `quantity` must be greater than zero;
5. `total_weight_kg` must be greater than zero;
6. `priority` must contain a supported value;
7. `status` must contain a supported value;
8. `created_at` must be a valid timestamp;
9. `deadline`, when provided, must be later than `created_at`.

### 5.7 Example

```json
{
  "order_id": "O101",
  "product_id": "P15",
  "shelf_id": "S7",
  "quantity": 2,
  "total_weight_kg": 20.0,
  "priority": "urgent",
  "status": "pending",
  "created_at": "2026-07-01T13:50:00Z",
  "deadline": "2026-07-01T14:30:00Z"
}
```

## 6. Robot Contract

The Robot contract represents the current operational state of a warehouse robot.

### 6.1 Producer

```text
Database Access Module
Backend API
```

### 6.2 Consumers

```text
Integration and Orchestration Module
Expert System Module
Route Planning Module
Robot Assignment Module
```

### 6.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `robot_id` | string | Yes | Unique robot identifier |
| `current_zone_id` | string | Yes | Current warehouse zone |
| `battery_level` | number | Yes | Battery percentage |
| `maximum_load_kg` | number | Yes | Maximum load capacity |
| `current_load_kg` | number | Yes | Current carried load |
| `current_workload` | integer | Yes | Number of active tasks |
| `status` | string | Yes | Operational robot status |
| `updated_at` | string | Yes | Last state update time |

### 6.4 Allowed Status Values

```text
available
busy
charging
failed
maintenance
```

### 6.5 Validation Rules

1. `robot_id` must not be empty;
2. `current_zone_id` must not be empty;
3. `battery_level` must be between 0 and 100;
4. `maximum_load_kg` must be greater than zero;
5. `current_load_kg` must be zero or greater;
6. `current_load_kg` must not exceed `maximum_load_kg`;
7. `current_workload` must be zero or greater;
8. `status` must contain a supported value;
9. `updated_at` must be a valid timestamp.

### 6.6 Example

```json
{
  "robot_id": "R1",
  "current_zone_id": "ZONE-A",
  "battery_level": 82.5,
  "maximum_load_kg": 50.0,
  "current_load_kg": 0.0,
  "current_workload": 0,
  "status": "available",
  "updated_at": "2026-07-01T13:54:00Z"
}
```

## 7. Product Contract

The Product contract represents a warehouse product.

### 7.1 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `product_id` | string | Yes | Unique product identifier |
| `name` | string | Yes | Human-readable product name |
| `unit_weight_kg` | number | Yes | Weight of one unit |
| `active` | boolean | Yes | Whether the product is active |

### 7.2 Example

```json
{
  "product_id": "P15",
  "name": "Electronic Component Box",
  "unit_weight_kg": 10.0,
  "active": true
}
```

## 8. Shelf Contract

The Shelf contract represents stored information about a warehouse shelf.

### 8.1 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `shelf_id` | string | Yes | Unique shelf identifier |
| `zone_id` | string | Yes | Warehouse zone containing the shelf |
| `product_id` | string | Yes | Product stored on the shelf |
| `status` | string | Yes | Current known shelf status |
| `available_quantity` | integer | Yes | Known product quantity |
| `last_updated_at` | string | Yes | Last update timestamp |

### 8.2 Allowed Status Values

```text
empty
low_stock
normal
full
unknown
```

### 8.3 Example

```json
{
  "shelf_id": "S7",
  "zone_id": "ZONE-B",
  "product_id": "P15",
  "status": "normal",
  "available_quantity": 30,
  "last_updated_at": "2026-07-01T13:55:00Z"
}
```

## 9. Warehouse Zone Contract

The Warehouse Zone contract represents a location in the warehouse graph.

### 9.1 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `zone_id` | string | Yes | Unique zone identifier |
| `name` | string | Yes | Human-readable zone name |
| `active` | boolean | Yes | Whether the zone is accessible |

### 9.2 Example

```json
{
  "zone_id": "ZONE-B",
  "name": "Storage Zone B",
  "active": true
}
```

## 10. Route Result Contract

The Route Planning module returns route information for one eligible robot.

### 10.1 Producer

```text
Route Planning Module
```

Owner:

```text
Halit
```

### 10.2 Consumers

```text
Integration and Orchestration Module
Robot Assignment Module
```

### 10.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `robot_id` | string | Yes | Robot for which the route was calculated |
| `start_zone_id` | string | Yes | Robot starting zone |
| `destination_zone_id` | string | Yes | Shelf destination zone |
| `route` | array of strings | Yes | Ordered zone identifiers |
| `distance_meters` | number | Yes | Total route distance |
| `estimated_travel_seconds` | number | Yes | Estimated travel time |
| `route_available` | boolean | Yes | Whether a valid route exists |

### 10.4 Validation Rules

1. distance must be zero or greater;
2. estimated travel time must be zero or greater;
3. route must not be empty when `route_available` is `true`;
4. route must begin with `start_zone_id`;
5. route must end with `destination_zone_id`.

### 10.5 Example

```json
{
  "robot_id": "R1",
  "start_zone_id": "ZONE-A",
  "destination_zone_id": "ZONE-B",
  "route": [
    "ZONE-A",
    "ZONE-C",
    "ZONE-B"
  ],
  "distance_meters": 45.0,
  "estimated_travel_seconds": 38.0,
  "route_available": true
}
```

### 10.6 Unavailable Route Example

```json
{
  "robot_id": "R4",
  "start_zone_id": "ZONE-D",
  "destination_zone_id": "ZONE-B",
  "route": [],
  "distance_meters": 0,
  "estimated_travel_seconds": 0,
  "route_available": false
}
```

## 11. Expert-System Fact Contract

The Orchestration module combines warehouse data and model results into structured facts.

### 11.1 Producer

```text
Integration and Orchestration Module
```

### 11.2 Consumer

```text
Expert System Module
```

### 11.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `order` | object | Yes | Order facts |
| `robots` | array | Yes | Candidate robot facts |
| `shelf` | object | Yes | Shelf facts |
| `forecast` | object | Yes | Forecast facts |
| `generated_at` | string | Yes | Fact-generation time |

### 11.4 Example

```json
{
  "order": {
    "order_id": "O101",
    "priority": "urgent",
    "total_weight_kg": 20.0,
    "shelf_id": "S7"
  },
  "robots": [
    {
      "robot_id": "R1",
      "battery_level": 82.5,
      "maximum_load_kg": 50.0,
      "current_zone_id": "ZONE-A",
      "current_workload": 0,
      "status": "available"
    },
    {
      "robot_id": "R2",
      "battery_level": 15.0,
      "maximum_load_kg": 30.0,
      "current_zone_id": "ZONE-B",
      "current_workload": 1,
      "status": "available"
    }
  ],
  "shelf": {
    "shelf_id": "S7",
    "zone_id": "ZONE-B",
    "status": "normal",
    "confidence": 0.91,
    "requires_manual_review": false
  },
  "forecast": {
    "expected_orders": 180,
    "load_level": "high"
  },
  "generated_at": "2026-07-01T13:56:00Z"
}
```

## 12. Expert-System Result Contract

The Expert System returns eligible robots, rejected robots, and logical explanations.

### 12.1 Producer

```text
Expert System Module
```

Owner:

```text
Halit
```

### 12.2 Consumer

```text
Integration and Orchestration Module
```

### 12.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `order_id` | string | Yes | Evaluated order identifier |
| `eligible_robot_ids` | array of strings | Yes | Robots that passed mandatory rules |
| `rejected_robots` | array of objects | Yes | Rejected robots and reasons |
| `applied_rules` | array of strings | Yes | Rule identifiers used |
| `decision_constraints` | array of strings | Yes | Conclusions affecting assignment |
| `evaluated_at` | string | Yes | Evaluation timestamp |

### 12.4 Example

```json
{
  "order_id": "O101",
  "eligible_robot_ids": [
    "R1",
    "R3"
  ],
  "rejected_robots": [
    {
      "robot_id": "R2",
      "reasons": [
        "Battery level is below the minimum threshold."
      ]
    }
  ],
  "applied_rules": [
    "RULE-ROBOT-AVAILABLE",
    "RULE-MIN-BATTERY",
    "RULE-LOAD-CAPACITY",
    "RULE-SHELF-NOT-EMPTY"
  ],
  "decision_constraints": [
    "Shelf is available.",
    "Manual review is not required."
  ],
  "evaluated_at": "2026-07-01T13:56:01Z"
}
```

## 13. Robot Ranking Input Contract

The Robot Assignment module receives eligible robots and route information.

### 13.1 Producer

```text
Integration and Orchestration Module
```

### 13.2 Consumer

```text
Robot Assignment Module
```

### 13.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `order` | object | Yes | Order information |
| `forecast` | object | Yes | Warehouse load information |
| `candidates` | array | Yes | Eligible robots with route data |
| `requested_at` | string | Yes | Ranking request timestamp |

### 13.4 Example

```json
{
  "order": {
    "order_id": "O101",
    "priority": "urgent",
    "total_weight_kg": 20.0
  },
  "forecast": {
    "expected_orders": 180,
    "load_level": "high"
  },
  "candidates": [
    {
      "robot_id": "R1",
      "battery_level": 82.5,
      "current_workload": 0,
      "distance_meters": 45.0,
      "estimated_travel_seconds": 38.0
    },
    {
      "robot_id": "R3",
      "battery_level": 70.0,
      "current_workload": 1,
      "distance_meters": 30.0,
      "estimated_travel_seconds": 27.0
    }
  ],
  "requested_at": "2026-07-01T13:56:02Z"
}
```

## 14. Robot Ranking Result Contract

The Robot Assignment module returns ranked robots and the selected candidate.

### 14.1 Producer

```text
Robot Assignment Module
```

Owner:

```text
Halit
```

### 14.2 Consumer

```text
Integration and Orchestration Module
```

### 14.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `order_id` | string | Yes | Order identifier |
| `selected_robot_id` | string or null | Yes | Selected robot or null |
| `ranked_candidates` | array | Yes | Robots ordered by score |
| `assignment_possible` | boolean | Yes | Whether assignment is possible |
| `reason` | string | Yes | Final ranking result explanation |
| `generated_at` | string | Yes | Ranking timestamp |

### 14.4 Example

```json
{
  "order_id": "O101",
  "selected_robot_id": "R1",
  "ranked_candidates": [
    {
      "robot_id": "R1",
      "score": 86.4,
      "score_components": {
        "battery_score": 24.8,
        "distance_score": 22.0,
        "workload_score": 20.0,
        "priority_score": 19.6
      }
    },
    {
      "robot_id": "R3",
      "score": 78.1,
      "score_components": {
        "battery_score": 21.0,
        "distance_score": 25.0,
        "workload_score": 12.5,
        "priority_score": 19.6
      }
    }
  ],
  "assignment_possible": true,
  "reason": "Robot R1 received the highest ranking score.",
  "generated_at": "2026-07-01T13:56:03Z"
}
```

### 14.5 Rejection Example

```json
{
  "order_id": "O101",
  "selected_robot_id": null,
  "ranked_candidates": [],
  "assignment_possible": false,
  "reason": "No eligible robot is available.",
  "generated_at": "2026-07-01T13:56:03Z"
}
```

## 15. Final Assignment Decision Contract

The Orchestration module returns the final assignment response through the Backend API.

### 15.1 Producer

```text
Integration and Orchestration Module
```

### 15.2 Consumers

```text
Backend API
Database Access Module
```

### 15.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `decision_id` | string | Yes | Unique decision identifier |
| `assignment_id` | string or null | Yes | Created assignment identifier |
| `order_id` | string | Yes | Order identifier |
| `decision` | string | Yes | Assignment decision |
| `selected_robot_id` | string or null | Yes | Selected robot |
| `route` | array of strings | Yes | Selected route |
| `distance_meters` | number or null | Yes | Route distance |
| `forecast_summary` | object | Yes | Forecast information used |
| `shelf_summary` | object | Yes | Shelf prediction used |
| `rejected_robots` | array | Yes | Rejected robots and reasons |
| `explanation` | array of strings | Yes | Human-readable reasoning |
| `created_at` | string | Yes | Decision timestamp |

### 15.4 Allowed Decision Values

```text
assigned
rejected
manual_review_required
```

### 15.5 Successful Assignment Example

```json
{
  "decision_id": "D9001",
  "assignment_id": "A501",
  "order_id": "O101",
  "decision": "assigned",
  "selected_robot_id": "R1",
  "route": [
    "ZONE-A",
    "ZONE-C",
    "ZONE-B"
  ],
  "distance_meters": 45.0,
  "forecast_summary": {
    "expected_orders": 180,
    "load_level": "high"
  },
  "shelf_summary": {
    "shelf_id": "S7",
    "status": "normal",
    "confidence": 0.91
  },
  "rejected_robots": [
    {
      "robot_id": "R2",
      "reasons": [
        "Battery level is below the minimum threshold."
      ]
    }
  ],
  "explanation": [
    "Shelf S7 contains the required product.",
    "Shelf recognition confidence is sufficient.",
    "Robot R1 is operational and available.",
    "Robot R1 has sufficient battery and load capacity.",
    "Robot R1 received the highest ranking score."
  ],
  "created_at": "2026-07-01T13:56:04Z"
}
```

### 15.6 Manual Review Example

```json
{
  "decision_id": "D9002",
  "assignment_id": null,
  "order_id": "O102",
  "decision": "manual_review_required",
  "selected_robot_id": null,
  "route": [],
  "distance_meters": null,
  "forecast_summary": {
    "expected_orders": 120,
    "load_level": "medium"
  },
  "shelf_summary": {
    "shelf_id": "S8",
    "status": "unknown",
    "confidence": 0.42
  },
  "rejected_robots": [],
  "explanation": [
    "Shelf recognition confidence is below the configured threshold.",
    "Manual inspection is required before robot assignment."
  ],
  "created_at": "2026-07-01T13:56:04Z"
}
```

## 16. Robot Failure Event Contract

The Robot Failure Event contract triggers replanning.

### 16.1 Producer

```text
Backend API
Database Access Module
```

### 16.2 Consumer

```text
Integration and Orchestration Module
```

### 16.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `robot_id` | string | Yes | Failed robot identifier |
| `assignment_id` | string | Yes | Active assignment |
| `order_id` | string | Yes | Affected order |
| `previous_status` | string | Yes | Previous robot status |
| `new_status` | string | Yes | New robot status |
| `failure_reason` | string | Yes | Failure description |
| `detected_at` | string | Yes | Failure timestamp |

### 16.4 Example

```json
{
  "robot_id": "R1",
  "assignment_id": "A501",
  "order_id": "O101",
  "previous_status": "busy",
  "new_status": "failed",
  "failure_reason": "Motor malfunction detected.",
  "detected_at": "2026-07-01T14:02:00Z"
}
```

## 17. Replanning Result Contract

The system returns a new decision after robot failure.

### 17.1 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `previous_assignment_id` | string | Yes | Failed assignment |
| `new_assignment_id` | string or null | Yes | New assignment |
| `order_id` | string | Yes | Affected order |
| `failed_robot_id` | string | Yes | Failed robot |
| `replacement_robot_id` | string or null | Yes | Replacement robot |
| `status` | string | Yes | Replanning result |
| `explanation` | array of strings | Yes | Replanning explanation |
| `replanned_at` | string | Yes | Replanning timestamp |

### 17.2 Allowed Status Values

```text
reassigned
reassignment_failed
```

### 17.3 Example

```json
{
  "previous_assignment_id": "A501",
  "new_assignment_id": "A502",
  "order_id": "O101",
  "failed_robot_id": "R1",
  "replacement_robot_id": "R3",
  "status": "reassigned",
  "explanation": [
    "Robot R1 was excluded because its status changed to failed.",
    "Robot R3 was selected as the highest-ranked remaining candidate."
  ],
  "replanned_at": "2026-07-01T14:02:02Z"
}
```

## 18. Rule Contract

The Rule contract represents one externally stored expert-system rule.

### 18.1 Producer

```text
Knowledge Engineer
Backend API
```

### 18.2 Consumer

```text
Expert System Module
```

### 18.3 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `rule_id` | string | Yes | Unique rule identifier |
| `name` | string | Yes | Human-readable rule name |
| `description` | string | Yes | Rule purpose |
| `conditions` | array | Yes | Required conditions |
| `actions` | array | Yes | Actions generated by the rule |
| `priority` | integer | Yes | Rule evaluation priority |
| `active` | boolean | Yes | Whether the rule is active |
| `version` | string | Yes | Rule version |

### 18.4 Example

```json
{
  "rule_id": "RULE-MIN-BATTERY",
  "name": "Minimum Battery Rule",
  "description": "Reject robots with battery below the configured threshold.",
  "conditions": [
    {
      "field": "robot.battery_level",
      "operator": "less_than",
      "value": 20
    }
  ],
  "actions": [
    {
      "type": "reject_robot",
      "reason": "Battery level is below the minimum threshold."
    }
  ],
  "priority": 100,
  "active": true,
  "version": "1.0"
}
```

## 19. Rule Reload Result Contract

The system returns the result of reloading external rules.

### 19.1 Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `success` | boolean | Yes | Whether reload succeeded |
| `loaded_rules` | integer | Yes | Number of loaded rules |
| `rejected_rules` | integer | Yes | Number of invalid rules |
| `errors` | array | Yes | Rule-validation errors |
| `reloaded_at` | string | Yes | Reload timestamp |

### 19.2 Example

```json
{
  "success": true,
  "loaded_rules": 11,
  "rejected_rules": 0,
  "errors": [],
  "reloaded_at": "2026-07-01T14:05:00Z"
}
```

## 20. Contract Ownership

| Contract | Primary owner | Reviewer |
|---|---|---|
| Forecast Result | Abdelrahman | Halit |
| Shelf Recognition Result | Abdelrahman | Halit |
| Order | Halit | Abdelrahman |
| Robot | Halit | Abdelrahman |
| Product | Halit | Abdelrahman |
| Shelf | Halit | Abdelrahman |
| Warehouse Zone | Halit | Abdelrahman |
| Route Result | Halit | Abdelrahman |
| Expert-System Fact | Shared | Shared |
| Expert-System Result | Halit | Abdelrahman |
| Robot Ranking Input | Shared | Shared |
| Robot Ranking Result | Halit | Abdelrahman |
| Final Assignment Decision | Shared | Shared |
| Robot Failure Event | Halit | Abdelrahman |
| Replanning Result | Halit | Abdelrahman |
| Rule | Halit | Abdelrahman |
| Rule Reload Result | Halit | Abdelrahman |

## 21. Versioning Rules

Data contracts follow semantic-style versioning.

Examples:

```text
0.1
0.2
1.0
```

Rules:

1. documentation corrections may increment the patch version;
2. backward-compatible field additions may increment the minor version;
3. breaking field changes must increment the major version;
4. consumers must be updated before a breaking contract is merged;
5. all contract changes must be reviewed by both participants.

## 22. Change Process

A contract change must include:

- changed contract name;
- old field or behavior;
- new field or behavior;
- reason for the change;
- affected modules;
- required code changes;
- compatibility impact.

Approved changes must update the document version.

## 23. Approval Status

All contracts in version `0.1` are currently:

```text
Proposed
```

They become:

```text
Approved
```

after review by Abdelrahman and Halit.