# Data Dictionary

## Document Information

| Field | Value |
|---|---|
| Project name | Hybrid Intelligent Warehouse System |
| Document version | 0.1 |
| Document type | Central Data Dictionary |
| Team | Abdelrahman and Halit |
| Current phase | Data design |

## 1. Purpose

This document defines the meaning, type, constraints, and ownership of the main data fields used in the Hybrid Intelligent Warehouse System.

The data dictionary provides a single reference for:

- database design;
- API request and response models;
- machine-learning outputs;
- expert-system facts;
- validation rules;
- automated tests;
- integration between modules.

Field names should remain consistent across the database, API, Python models, and data contracts whenever practical.

## 2. General Conventions

### 2.1 Naming Convention

Field names must use:

```text
snake_case
```

Examples:

```text
robot_id
battery_level
created_at
expected_orders
```

### 2.2 Timestamp Convention

All timestamps must use ISO 8601 format in UTC.

Example:

```text
2026-07-01T14:00:00Z
```

### 2.3 Identifier Convention

| Entity | Prefix | Example |
|---|---|---|
| Order | `O` | `O101` |
| Robot | `R` | `R1` |
| Product | `P` | `P15` |
| Shelf | `S` | `S7` |
| Zone | `ZONE-` | `ZONE-A` |
| Assignment | `A` | `A501` |
| Decision | `D` | `D9001` |
| Rule | `RULE-` | `RULE-001` |

### 2.4 Unit Convention

| Measurement | Unit |
|---|---|
| Weight | kilograms |
| Distance | meters |
| Travel time | seconds |
| Forecast horizon | minutes |
| Battery level | percentage |
| Confidence | decimal from 0 to 1 |

## 3. Order Entity

The Order entity represents one warehouse request that requires product retrieval.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `order_id` | string | Yes | Unique, non-empty | Unique order identifier |
| `product_id` | string | Yes | Existing product | Product required by the order |
| `shelf_id` | string | Yes | Existing shelf | Shelf containing the required product |
| `quantity` | integer | Yes | Greater than 0 | Number of required product units |
| `total_weight_kg` | number | Yes | Greater than 0 | Total weight of the order |
| `priority` | string | Yes | Supported enum value | Operational priority |
| `status` | string | Yes | Supported enum value | Current order state |
| `created_at` | datetime | Yes | ISO 8601 UTC | Order creation time |
| `deadline` | datetime or null | No | Later than `created_at` | Optional completion deadline |

### 3.1 Order Priority Values

```text
low
normal
high
urgent
```

### 3.2 Order Status Values

```text
pending
assigned
in_progress
completed
rejected
cancelled
```

### 3.3 Order Business Rules

- `quantity` must be greater than zero;
- `total_weight_kg` must be greater than zero;
- only orders with status `pending` may enter the initial assignment workflow;
- urgent orders receive increased ranking priority;
- rejected orders must include a rejection reason.

## 4. Robot Entity

The Robot entity represents the current operational state of one warehouse robot.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `robot_id` | string | Yes | Unique, non-empty | Unique robot identifier |
| `current_zone_id` | string | Yes | Existing active zone | Current robot location |
| `battery_level` | number | Yes | Between 0 and 100 | Current battery percentage |
| `maximum_load_kg` | number | Yes | Greater than 0 | Maximum supported load |
| `current_load_kg` | number | Yes | Between 0 and maximum load | Current carried weight |
| `current_workload` | integer | Yes | Zero or greater | Number of active tasks |
| `status` | string | Yes | Supported enum value | Current operational status |
| `updated_at` | datetime | Yes | ISO 8601 UTC | Last robot-state update |

### 4.1 Robot Status Values

```text
available
busy
charging
failed
maintenance
```

### 4.2 Robot Business Rules

- only robots with status `available` may receive a new assignment;
- battery level must meet the configured minimum threshold;
- maximum load must support the order weight;
- failed robots must be excluded from ranking;
- `current_load_kg` must not exceed `maximum_load_kg`;
- assignment logic must use the most recently updated robot state.

## 5. Product Entity

The Product entity represents one product stored in the warehouse.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `product_id` | string | Yes | Unique, non-empty | Unique product identifier |
| `name` | string | Yes | Non-empty | Human-readable product name |
| `unit_weight_kg` | number | Yes | Greater than 0 | Weight of one product unit |
| `active` | boolean | Yes | `true` or `false` | Whether the product is currently active |

### 5.1 Product Business Rules

- inactive products cannot be used in new orders;
- `unit_weight_kg` must be greater than zero;
- order total weight may be calculated as quantity multiplied by unit weight.

## 6. Shelf Entity

The Shelf entity represents one warehouse storage shelf.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `shelf_id` | string | Yes | Unique, non-empty | Unique shelf identifier |
| `zone_id` | string | Yes | Existing zone | Zone containing the shelf |
| `product_id` | string | Yes | Existing product | Product stored on the shelf |
| `status` | string | Yes | Supported enum value | Current shelf state |
| `available_quantity` | integer | Yes | Zero or greater | Available product quantity |
| `last_updated_at` | datetime | Yes | ISO 8601 UTC | Last shelf-data update |

### 6.1 Shelf Status Values

```text
empty
low_stock
normal
full
unknown
```

### 6.2 Shelf Business Rules

- `empty` prevents product picking;
- `unknown` may require manual inspection;
- `available_quantity` must be zero when status is `empty`;
- a shelf must belong to one warehouse zone;
- the MVP associates one primary product with one shelf.

## 7. Warehouse Zone Entity

The Warehouse Zone entity represents one location in the warehouse graph.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `zone_id` | string | Yes | Unique, non-empty | Unique warehouse-zone identifier |
| `name` | string | Yes | Non-empty | Human-readable zone name |
| `active` | boolean | Yes | `true` or `false` | Whether the zone is accessible |

### 7.1 Zone Business Rules

- inactive zones must not be used in route calculation;
- every robot and shelf must reference a valid zone;
- zones are graph nodes in the routing module.

## 8. Warehouse Path Entity

The Warehouse Path entity represents a connection between two zones.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `path_id` | string | Yes | Unique, non-empty | Unique path identifier |
| `start_zone_id` | string | Yes | Existing zone | Path starting zone |
| `end_zone_id` | string | Yes | Existing zone | Path destination zone |
| `distance_meters` | number | Yes | Greater than 0 | Physical path distance |
| `estimated_travel_seconds` | number | Yes | Greater than 0 | Estimated travel time |
| `active` | boolean | Yes | `true` or `false` | Whether the path is usable |

### 8.1 Path Business Rules

- negative or zero distances are invalid;
- inactive paths must not be used;
- a path must connect two valid zones;
- route calculation uses path distance as the initial edge weight.

## 9. Forecast Entity

The Forecast entity represents one workload prediction.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `forecast_id` | string | Yes | Unique | Unique prediction identifier |
| `forecast_time` | datetime | Yes | ISO 8601 UTC | Start of predicted interval |
| `forecast_horizon_minutes` | integer | Yes | Greater than 0 | Prediction duration |
| `expected_orders` | integer | Yes | Zero or greater | Predicted number of orders |
| `load_level` | string | Yes | Supported enum value | Workload classification |
| `model_version` | string | Yes | Non-empty | Forecasting-model version |
| `generated_at` | datetime | Yes | ISO 8601 UTC | Prediction generation time |

### 9.1 Load Level Values

```text
low
medium
high
```

### 9.2 Forecast Business Rules

- the MVP forecast horizon is 60 minutes;
- expected orders cannot be negative;
- load level must be derived using configured thresholds;
- forecast data must include the model version.

## 10. Shelf Prediction Entity

The Shelf Prediction entity stores one image-model result.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `prediction_id` | string | Yes | Unique | Unique prediction identifier |
| `shelf_id` | string | Yes | Existing shelf | Predicted shelf |
| `status` | string | Yes | Supported shelf status | Predicted condition |
| `confidence` | number | Yes | Between 0 and 1 | Prediction confidence |
| `requires_manual_review` | boolean | Yes | Derived value | Human-review indicator |
| `model_version` | string | Yes | Non-empty | Image-model version |
| `prediction_time` | datetime | Yes | ISO 8601 UTC | Prediction generation time |

### 10.1 Shelf Prediction Business Rules

- confidence below `0.60` requires manual review;
- uncertain predictions may use status `unknown`;
- prediction output must contain the model version;
- image-model results must not directly assign robots.

## 11. Assignment Entity

The Assignment entity represents the connection between an order and a selected robot.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `assignment_id` | string | Yes | Unique | Unique assignment identifier |
| `order_id` | string | Yes | Existing order | Assigned order |
| `robot_id` | string | Yes | Existing robot | Selected robot |
| `status` | string | Yes | Supported enum value | Assignment state |
| `score` | number | Yes | Zero or greater | Selected robot ranking score |
| `route_distance_meters` | number | Yes | Zero or greater | Selected route distance |
| `created_at` | datetime | Yes | ISO 8601 UTC | Assignment creation time |
| `completed_at` | datetime or null | No | Later than `created_at` | Assignment completion time |

### 11.1 Assignment Status Values

```text
assigned
in_progress
completed
failed
cancelled
reassigned
```

### 11.2 Assignment Business Rules

- one active assignment belongs to one order;
- failed assignments may trigger replanning;
- the selected robot must be eligible;
- assignment status changes must be stored;
- a completed assignment must have `completed_at`.

## 12. Decision Record Entity

The Decision Record entity stores the complete explainable system decision.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `decision_id` | string | Yes | Unique | Unique decision identifier |
| `order_id` | string | Yes | Existing order | Evaluated order |
| `assignment_id` | string or null | Yes | Existing assignment or null | Created assignment |
| `decision` | string | Yes | Supported enum value | Final decision |
| `selected_robot_id` | string or null | Yes | Existing robot or null | Selected robot |
| `explanation` | array of strings | Yes | Non-empty | Human-readable reasoning |
| `applied_rules` | array of strings | Yes | Rule identifiers | Rules used in the decision |
| `created_at` | datetime | Yes | ISO 8601 UTC | Decision timestamp |

### 12.1 Decision Values

```text
assigned
rejected
manual_review_required
```

### 12.2 Decision Business Rules

- every decision must have an explanation;
- rejected decisions must explain why assignment failed;
- manual-review decisions must identify the uncertainty;
- successful decisions must reference the selected robot;
- decision history must not be silently overwritten.

## 13. Rule Entity

The Rule entity represents one expert-system production rule.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `rule_id` | string | Yes | Unique | Unique rule identifier |
| `name` | string | Yes | Non-empty | Human-readable name |
| `description` | string | Yes | Non-empty | Rule purpose |
| `conditions` | array | Yes | Non-empty | Conditions evaluated by the engine |
| `actions` | array | Yes | Non-empty | Actions produced by the rule |
| `priority` | integer | Yes | Zero or greater | Evaluation priority |
| `active` | boolean | Yes | `true` or `false` | Whether the rule is active |
| `version` | string | Yes | Non-empty | Rule version |

### 13.1 Rule Condition Fields

A rule condition may contain:

| Field | Type | Description |
|---|---|---|
| `field` | string | Fact field being evaluated |
| `operator` | string | Comparison operator |
| `value` | any | Expected comparison value |

### 13.2 Supported Rule Operators

```text
equals
not_equals
greater_than
greater_than_or_equal
less_than
less_than_or_equal
in
not_in
```

### 13.3 Rule Business Rules

- inactive rules must not be evaluated;
- invalid rules must be rejected during loading;
- each rule must have at least one condition and one action;
- rule changes must not require rebuilding the application;
- rule versions must be tracked.

## 14. Route Result Object

The Route Result object represents one calculated route.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `robot_id` | string | Yes | Existing robot | Robot for which route was calculated |
| `start_zone_id` | string | Yes | Existing zone | Route start |
| `destination_zone_id` | string | Yes | Existing zone | Route destination |
| `route` | array of strings | Yes | Ordered zones | Calculated route |
| `distance_meters` | number | Yes | Zero or greater | Total route distance |
| `estimated_travel_seconds` | number | Yes | Zero or greater | Estimated travel time |
| `route_available` | boolean | Yes | `true` or `false` | Whether route exists |

### 14.1 Route Result Business Rules

- an available route must not be empty;
- the first route node must equal `start_zone_id`;
- the final route node must equal `destination_zone_id`;
- unavailable routes use an empty route list;
- unavailable routes must not proceed to final ranking.

## 15. Robot Ranking Candidate Object

The Robot Ranking Candidate object represents one eligible robot with ranking information.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `robot_id` | string | Yes | Existing eligible robot | Candidate identifier |
| `battery_level` | number | Yes | Between 0 and 100 | Current battery |
| `current_workload` | integer | Yes | Zero or greater | Active task count |
| `distance_meters` | number | Yes | Zero or greater | Route distance |
| `estimated_travel_seconds` | number | Yes | Zero or greater | Travel-time estimate |
| `score` | number or null | No | Numeric | Calculated ranking score |
| `score_components` | object or null | No | Structured object | Score breakdown |

## 16. Robot Rejection Object

The Robot Rejection object represents one rejected robot and the reasons for rejection.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `robot_id` | string | Yes | Existing robot | Rejected robot |
| `reasons` | array of strings | Yes | Non-empty | Rejection reasons |
| `applied_rules` | array of strings | No | Rule identifiers | Rules causing rejection |

## 17. Robot Failure Event

The Robot Failure Event represents a robot-state change that triggers replanning.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `robot_id` | string | Yes | Existing robot | Failed robot |
| `assignment_id` | string | Yes | Active assignment | Affected assignment |
| `order_id` | string | Yes | Existing order | Affected order |
| `previous_status` | string | Yes | Supported status | Previous robot status |
| `new_status` | string | Yes | Must be `failed` | New robot status |
| `failure_reason` | string | Yes | Non-empty | Failure description |
| `detected_at` | datetime | Yes | ISO 8601 UTC | Failure detection time |

## 18. Replanning Result Object

The Replanning Result object represents the outcome of replacing a failed robot.

| Field | Type | Required | Constraints | Description |
|---|---|---:|---|---|
| `previous_assignment_id` | string | Yes | Existing assignment | Failed assignment |
| `new_assignment_id` | string or null | Yes | New assignment or null | Replacement assignment |
| `order_id` | string | Yes | Existing order | Affected order |
| `failed_robot_id` | string | Yes | Existing robot | Failed robot |
| `replacement_robot_id` | string or null | Yes | Existing robot or null | Selected replacement |
| `status` | string | Yes | Supported enum | Replanning result |
| `explanation` | array of strings | Yes | Non-empty | Replanning explanation |
| `replanned_at` | datetime | Yes | ISO 8601 UTC | Replanning time |

### 18.1 Replanning Status Values

```text
reassigned
reassignment_failed
```

## 19. Shared Enumeration Summary

### 19.1 Order Priority

```text
low
normal
high
urgent
```

### 19.2 Order Status

```text
pending
assigned
in_progress
completed
rejected
cancelled
```

### 19.3 Robot Status

```text
available
busy
charging
failed
maintenance
```

### 19.4 Shelf Status

```text
empty
low_stock
normal
full
unknown
```

### 19.5 Warehouse Load Level

```text
low
medium
high
```

### 19.6 Assignment Status

```text
assigned
in_progress
completed
failed
cancelled
reassigned
```

### 19.7 Decision Type

```text
assigned
rejected
manual_review_required
```

### 19.8 Replanning Status

```text
reassigned
reassignment_failed
```

## 20. Configuration Fields

The following values should be configurable rather than hardcoded.

| Field | Type | Initial Value | Description |
|---|---|---:|---|
| `minimum_battery_level` | number | `20` | Minimum battery required for assignment |
| `manual_review_threshold` | number | `0.60` | Minimum trusted image confidence |
| `forecast_horizon_minutes` | integer | `60` | Forecast duration |
| `low_load_threshold` | integer | To be defined | Maximum expected orders for low load |
| `high_load_threshold` | integer | To be defined | Minimum expected orders for high load |
| `default_robot_speed_mps` | number | To be defined | Used for travel-time estimation |

## 21. Field Ownership

| Data group | Primary owner | Reviewer |
|---|---|---|
| Forecast fields | Abdelrahman | Halit |
| Shelf-prediction fields | Abdelrahman | Halit |
| Order fields | Halit | Abdelrahman |
| Robot fields | Halit | Abdelrahman |
| Product fields | Halit | Abdelrahman |
| Shelf storage fields | Halit | Abdelrahman |
| Zone and path fields | Halit | Abdelrahman |
| Assignment fields | Halit | Abdelrahman |
| Expert-system facts | Shared | Shared |
| Final-decision fields | Shared | Shared |

## 22. Database Mapping Guidance

The following data groups are expected to become database tables:

```text
orders
robots
products
shelves
zones
warehouse_paths
forecasts
shelf_predictions
assignments
decision_records
rules
```

The following structures are expected to remain request or response objects rather than independent tables:

```text
route_result
robot_ranking_candidate
robot_rejection
replanning_result
```

This mapping may change after database-schema review.

## 23. Validation Responsibility

Validation must happen at multiple levels:

1. API validation using Pydantic models;
2. business validation inside application services;
3. database validation using constraints;
4. model-output validation before integration;
5. rule validation before rule loading.

No module should assume that external input is valid without checking it.

## 24. Versioning

This data dictionary follows the same versioning rules as:

```text
docs/data_contracts.md
```

Breaking changes to field names, types, or meanings require:

- review by both participants;
- update of affected data contracts;
- update of API schemas;
- update of database migrations;
- update of automated tests;
- document-version increment.

## 25. Approval Status

All definitions in version `0.1` are currently:

```text
Proposed
```

They become:

```text
Approved
```

after review by Abdelrahman and Halit.