# Final Machine Learning Contracts

## 1. Purpose

This document defines the final contracts between:

- forecasting;
- shelf recognition;
- ML integration;
- expert-system reasoning;
- backend services.

The contracts separate module responsibilities and prevent downstream code from depending on internal model implementation.

---

## 2. Contract Principles

All ML-facing contracts must follow these rules:

1. fields have stable names;
2. values have explicit types;
3. timestamps include timezone information;
4. confidence values remain between `0.0` and `1.0`;
5. model versions are included;
6. invalid values are rejected;
7. uncertain predictions trigger manual review;
8. modules communicate through schemas;
9. model internals are not exposed to the expert system;
10. failed or unavailable ML inputs use explicit fallback behavior.

---

## 3. ForecastResult

### Purpose

Represents the result of short-term order forecasting.

### Fields

| Field | Type | Meaning |
|---|---|---|
| `forecast_time` | timezone-aware datetime | Time for which demand is forecast |
| `forecast_horizon_minutes` | integer | Forecast horizon |
| `expected_orders` | integer | Predicted order count |
| `load_level` | enum/string | `low`, `medium`, or `high` |
| `model_version` | string | Forecasting model identifier |
| `generated_at` | timezone-aware datetime | Result-generation time |

### Validation Rules

- timestamps must include timezone information;
- forecast horizon must be positive;
- expected orders must not be negative;
- load level must be supported;
- model version must not be empty.

### Example

```json
{
  "forecast_time": "2026-07-12T12:00:00+00:00",
  "forecast_horizon_minutes": 60,
  "expected_orders": 24,
  "load_level": "low",
  "model_version": "random-forest-1.0",
  "generated_at": "2026-07-12T11:55:00+00:00"
}
```

---

## 4. ShelfPredictionResult

### Purpose

Represents the predicted operational state of a shelf.

### Fields

| Field | Type | Meaning |
|---|---|---|
| `shelf_id` | string | Target shelf identifier |
| `status` | enum/string | Predicted shelf status |
| `confidence` | float | Confidence between 0 and 1 |
| `model_version` | string | Recognition model identifier |
| `prediction_time` | timezone-aware datetime | Prediction time |
| `requires_manual_review` | boolean | Whether automatic processing must stop |

### Validation Rules

- shelf identifier must not be empty;
- confidence must be between `0.0` and `1.0`;
- prediction time must include timezone information;
- confidence below `0.60` requires manual review;
- unavailable-image fallback uses `unknown`;
- fallback results must not claim high confidence.

### Safe Fallback Example

```json
{
  "shelf_id": "S1",
  "status": "unknown",
  "confidence": 0.0,
  "model_version": "no-image-fallback-1.0",
  "prediction_time": "2026-07-12T11:55:00+00:00",
  "requires_manual_review": true
}
```

---

## 5. Expert-System Fact Contracts

The expert system receives a simplified and validated representation rather than raw ML objects.

---

### 5.1 OrderFacts

| Field | Type | Meaning |
|---|---|---|
| `order_id` | string | Order identifier |
| `priority` | enum/string | Order priority |
| `total_weight_kg` | float | Required payload |
| `shelf_id` | string | Target shelf |

---

### 5.2 RobotFacts

| Field | Type | Meaning |
|---|---|---|
| `robot_id` | string | Robot identifier |
| `battery_level` | numeric | Current battery level |
| `maximum_load_kg` | numeric | Maximum payload |
| `current_zone_id` | string | Current warehouse zone |
| `current_workload` | numeric | Current assigned workload |
| `status` | enum/string | Operational status |

Robot identifiers must be unique within one fact set.

---

### 5.3 ShelfFacts

| Field | Type | Meaning |
|---|---|---|
| `shelf_id` | string | Target shelf identifier |
| `zone_id` | string | Shelf zone |
| `status` | enum/string | Predicted status |
| `confidence` | float | Recognition confidence |
| `requires_manual_review` | boolean | Safety control |

The shelf identifier must match the order target shelf.

---

### 5.4 ForecastFacts

| Field | Type | Meaning |
|---|---|---|
| `expected_orders` | integer | Forecast demand |
| `load_level` | enum/string | Operational load category |

The expert system does not require forecasting features or model internals.

---

### 5.5 ExpertSystemFacts

| Field | Type | Meaning |
|---|---|---|
| `order` | `OrderFacts` | Current order |
| `robots` | list of `RobotFacts` | Candidate robots |
| `shelf` | `ShelfFacts` | Target shelf state |
| `forecast` | `ForecastFacts` | Forecast context |
| `generated_at` | timezone-aware datetime | Fact-set generation time |

### Integration Validation Rules

- at least one robot is required;
- robot identifiers must be unique;
- order shelf and physical shelf must match;
- order shelf and shelf prediction must match;
- generation timestamp must include timezone information;
- malformed ML output must fail before expert reasoning.

---

## 6. Module Ownership

### Forecasting owns

- model training;
- feature engineering;
- numerical prediction;
- load-level generation;
- forecast metadata.

### Shelf recognition owns

- image validation;
- status prediction;
- confidence;
- model version;
- manual-review decision;
- unavailable-image fallback.

### ML integration owns

- identifier consistency;
- fact transformation;
- duplicate detection;
- timezone validation;
- expert-system input construction.

### Expert system owns

- battery thresholds;
- payload rules;
- availability rules;
- candidate rejection;
- decision explanations;
- operational ranking policies.

The forecasting model must not directly select a robot.

The recognition model must not directly approve an assignment.

---

## 7. Failure Contracts

### Invalid forecast

Examples:

- negative expected orders;
- unsupported load level;
- missing timezone;
- empty model version.

Required behavior:

```text
Reject the result before expert-system execution.
```

### Invalid shelf prediction

Examples:

- confidence below zero;
- confidence above one;
- mismatched shelf identifier;
- low confidence without manual review;
- missing timezone.

Required behavior:

```text
Reject the result or replace it with a documented fallback.
```

### No shelf image

Required result:

```text
status = unknown
confidence = 0.0
requires_manual_review = true
```

### Forecasting service unavailable

Required system behavior should be explicit.

Recommended prototype fallback:

```text
Use a configured default load level,
record the forecasting failure,
and mark the decision as using fallback context.
```

The fallback policy belongs to service orchestration and must not be hidden inside the expert rules.

---

## 8. Versioning

Every model output contains `model_version`.

Recommended format:

```text
component-model-major.minor
```

Examples:

```text
forecast-random-forest-1.0
shelf-cnn-1.0
shelf-no-image-fallback-1.0
```

Contract-breaking schema changes should use a new API or schema version.

Model replacement that preserves the schema does not require changing expert-system code.

---

## 9. Boundary Cases

The contracts must support or reject the following cases predictably:

| Case | Expected behavior |
|---|---|
| `expected_orders = 0` | valid |
| `expected_orders < 0` | invalid |
| `confidence = 0.0` | valid with manual review |
| `confidence = 1.0` | valid |
| `confidence < 0.0` | invalid |
| `confidence > 1.0` | invalid |
| confidence below `0.60` | manual review required |
| naive datetime | invalid |
| duplicate robot IDs | invalid integration input |
| empty robot list | invalid integration input |
| shelf mismatch | invalid integration input |
| unknown shelf state | stop automatic assignment |

---

## 10. Backend Contract Expectations

The backend should:

1. accept validated request schemas;
2. call model services through service interfaces;
3. convert outputs through ML integration;
4. return validation errors clearly;
5. preserve timestamps and model versions;
6. distinguish invalid input from manual-review results;
7. avoid exposing model binary details;
8. log fallback use.

Example response distinction:

```text
HTTP validation failure:
The request or generated contract is invalid.

Operational manual review:
The contract is valid, but automatic assignment is unsafe.
```

These are not the same situation and should not share one vague error message.

---

## 11. Contract Acceptance Checklist

The ML contracts are accepted when:

- forecasting produces `ForecastResult`;
- shelf recognition produces `ShelfPredictionResult`;
- low confidence requires review;
- all timestamps are timezone-aware;
- ML integration produces `ExpertSystemFacts`;
- identifiers are checked;
- duplicate robots are rejected;
- invalid numerical boundaries are tested;
- the backend consumes contracts without model-specific assumptions;
- documentation matches the implemented schemas.
