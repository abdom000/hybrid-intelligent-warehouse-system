# System Scenarios

## 1. Purpose

This document defines the main operational scenarios for the Hybrid Intelligent Warehouse System.

Each scenario contains:

- initial conditions;
- system input;
- expected behavior;
- expected result;
- implementation status.

The scenarios separate valid operational outcomes from invalid data. A valid `manual_review` result is not the same as a schema-validation failure, despite software systems frequently trying to reduce everything to one unhelpful red error.

---

## 2. Scenario Status Labels

- **Implemented**: supported by the current code and automated tests.
- **Partially implemented**: input contracts and expected behavior are defined, but the final expert-system or assignment step is not yet connected.
- **Planned**: depends on backend, routing, database, or replanning work.

---

## 3. Scenario S1: Normal Order

### Initial Conditions

- order references an existing shelf;
- at least one robot is available;
- robot identifiers are unique;
- shelf prediction belongs to the order shelf;
- shelf confidence is sufficient;
- forecast result is valid.

### Expected Behavior

1. validate the order, shelf, robots, forecast, and shelf prediction;
2. build `ExpertSystemFacts`;
3. pass the facts to the expert system;
4. evaluate robot eligibility;
5. calculate routes;
6. select the best valid robot.

### Expected Result

```text
assignment_status = assigned
manual_review = false
selected_robot_id = a valid eligible robot
decision_reason = explanation of selection
```

### Status

Partially implemented.

The current system builds validated `ExpertSystemFacts`. Final robot selection depends on the expert-system, routing, and assignment modules.

---

## 4. Scenario S2: High-Priority Order

### Initial Conditions

- order priority is high;
- multiple orders or candidates compete for capacity;
- warehouse forecast may indicate medium or high load.

### Expected Behavior

- the expert system preserves the order priority;
- the assignment policy gives the order preference when resources are constrained;
- safety constraints still apply;
- priority must not override battery, payload, shelf, or route safety.

### Expected Result

```text
high priority influences ranking
unsafe robot remains rejected
decision includes priority reason
```

### Status

Partially implemented.

Priority is included in `OrderFacts`. Ranking behavior belongs to the expert-system and assignment implementation.

---

## 5. Scenario S3: Heavy Order

### Initial Conditions

- order weight exceeds the payload capacity of one or more robots;
- at least one stronger robot may exist.

### Expected Behavior

- reject every robot whose maximum payload is below order weight;
- retain robots with sufficient capacity;
- return rejection reasons.

### Expected Result

If a valid robot exists:

```text
assignment_status = assigned
rejected_reasons include insufficient_payload
```

If no valid robot exists:

```text
assignment_status = no_suitable_robot
```

### Status

Partially implemented.

The required payload and robot capacities are present in the contracts. The expert rule is still expected.

---

## 6. Scenario S4: Low-Battery Robots

### Initial Conditions

- one or more robots have battery below the configured safety threshold.

### Expected Behavior

- reject low-battery robots;
- do not permit order priority to bypass the battery rule;
- evaluate remaining candidates.

### Expected Result

```text
rejected_reasons include low_battery
```

or:

```text
assignment_status = no_suitable_robot
```

### Status

Partially implemented.

Battery is available in `RobotFacts`; threshold logic belongs to the expert system.

---

## 7. Scenario S5: Unavailable Robot

### Initial Conditions

- a robot status indicates unavailable, failed, charging, maintenance, or another non-assignable state.

### Expected Behavior

- reject the robot before routing;
- include the status-based reason;
- evaluate other robots.

### Expected Result

```text
rejected_reasons include unavailable_status
```

### Status

Partially implemented.

Robot status is passed to the expert system.

---

## 8. Scenario S6: Shelf State Unknown

### Initial Conditions

- no usable shelf image exists, or the predictor cannot confirm the state;
- fallback prediction is returned.

### Current Fallback

```text
status = unknown
confidence = 0.0
requires_manual_review = true
```

### Expected Behavior

- build a valid fact set;
- preserve the unknown status;
- require manual review;
- stop automatic assignment.

### Expected Result

```text
assignment_status = manual_review
manual_review = true
```

### Status

Implemented at the ML contract and integration level.

The current end-to-end ML demo verifies the fallback and produces `ExpertSystemFacts`.

---

## 9. Scenario S7: Low-Confidence Shelf Prediction

### Initial Conditions

- shelf confidence is below `0.60`.

### Expected Behavior

- require manual review;
- reject a contract that reports low confidence without manual review;
- avoid automatic assignment.

### Expected Result

```text
requires_manual_review = true
```

### Status

Implemented at schema-validation level.

---

## 10. Scenario S8: Mismatched Shelf Prediction

### Initial Conditions

- order references shelf `S1`;
- supplied prediction references another shelf.

### Expected Behavior

- reject the integration request;
- do not create `ExpertSystemFacts`;
- do not run expert rules.

### Expected Result

```text
MLIntegrationError
```

### Status

Implemented and tested.

---

## 11. Scenario S9: Empty Robot Candidate List

### Initial Conditions

- order, shelf, forecast, and prediction are valid;
- no candidate robots are supplied.

### Expected Behavior

- reject fact construction;
- do not create a misleading assignment request.

### Expected Result

```text
MLIntegrationError
```

### Status

Implemented and tested.

---

## 12. Scenario S10: Duplicate Robot Identifiers

### Initial Conditions

- the robot list contains the same robot identifier more than once.

### Expected Behavior

- reject fact construction;
- prevent duplicate candidates from influencing ranking.

### Expected Result

```text
MLIntegrationError
```

### Status

Implemented and tested.

---

## 13. Scenario S11: High Warehouse Load

### Initial Conditions

- forecast load is `high`;
- multiple orders and robot workloads compete for resources.

### Expected Behavior

The expert and assignment layers should:

- prefer robots with lower workload;
- avoid assigning overloaded robots;
- consider route cost more strictly;
- preserve high-priority handling;
- explain load-related decisions.

### Expected Result

```text
decision includes high-load context
```

### Status

Partially implemented.

`ForecastFacts` already includes expected orders and load level.

---

## 14. Scenario S12: No Suitable Robot

### Initial Conditions

Every robot fails at least one rule:

- unavailable status;
- low battery;
- insufficient capacity;
- no valid route;
- excessive workload under policy.

### Expected Behavior

- return an operational result rather than a technical crash;
- include rejection reasons for all candidates;
- avoid selecting a robot.

### Expected Result

```text
assignment_status = no_suitable_robot
selected_robot_id = null
```

### Status

Planned.

Depends on expert-system and assignment results.

---

## 15. Scenario S13: No Route to Shelf

### Initial Conditions

- robot passes safety rules;
- warehouse graph contains no valid path to the shelf zone.

### Expected Behavior

- reject that robot for the current assignment;
- evaluate other candidates;
- return `no_suitable_robot` if no routed candidate remains.

### Expected Result

```text
rejected_reasons include no_route
```

### Status

Planned.

Depends on routing.

---

## 16. Scenario S14: Robot Failure After Assignment

### Initial Conditions

- a robot has already been assigned;
- a failure event marks it unavailable before completion.

### Expected Behavior

1. mark the assignment interrupted;
2. exclude the failed robot;
3. reload current robot states;
4. run rules and routing again;
5. create a replacement assignment;
6. escalate if no replacement exists.

### Expected Result

Success case:

```text
assignment_status = reassigned
```

Failure case:

```text
assignment_status = replanning_failed
```

### Status

Planned.

Depends on persistence, failure events, and replanning.

---

## 17. Scenario S15: Invalid Forecast Contract

### Initial Conditions

Examples:

- negative expected order count;
- unsupported load level;
- missing timezone;
- invalid forecast horizon.

### Expected Behavior

- fail schema validation;
- prevent invalid forecast data from reaching the expert system.

### Expected Result

```text
ValidationError
```

### Status

Implemented at contract level.

---

## 18. Scenario S16: Naive Timestamp

### Initial Conditions

- a model or integration timestamp has no timezone.

### Expected Behavior

- reject the value;
- require an explicit timezone.

### Expected Result

```text
ValidationError or MLIntegrationError
```

### Status

Implemented.

---

## 19. Scenario S17: Forecasting Service Failure

### Initial Conditions

- forecasting model cannot load or generate a prediction.

### Expected Behavior

The orchestration layer should:

- record the failure;
- use an explicit configured fallback only if allowed;
- mark the result as using fallback context;
- avoid silently inventing a successful model prediction.

### Expected Result

Either:

```text
assignment continues with documented forecast fallback
```

or:

```text
assignment request fails with a clear service error
```

### Status

Planned.

The fallback policy must be implemented by backend orchestration.

---

## 20. Scenario S18: Invalid Shelf Image

### Initial Conditions

- image path is missing;
- image cannot be opened;
- image format is invalid.

### Expected Behavior

- image validation fails;
- return or create a documented fallback;
- require manual review.

### Expected Result

```text
status = unknown
requires_manual_review = true
```

or a clear input error, depending on the calling endpoint.

### Status

Implemented in the shelf-recognition pipeline at validation and fallback level.

---

## 21. Scenario-to-Module Matrix

| Scenario | ML | Integration | Expert System | Routing | Assignment | Replanning |
|---|---:|---:|---:|---:|---:|---:|
| Normal order | Yes | Yes | Required | Required | Required | No |
| High priority | Contract | Yes | Required | Required | Required | No |
| Heavy order | Contract | Yes | Required | Optional | Required | No |
| Low battery | Contract | Yes | Required | Optional | Required | No |
| Shelf unknown | Yes | Yes | Required | No | Required | No |
| Shelf mismatch | Yes | Yes | No | No | No | No |
| Duplicate robots | No | Yes | No | No | No | No |
| High load | Yes | Yes | Required | Required | Required | No |
| No route | No | Yes | Required | Required | Required | No |
| Robot failure | No | Yes | Required | Required | Required | Required |

---

## 22. Acceptance Checklist

The scenario layer is accepted when:

- implemented scenarios have automated tests;
- planned scenarios have explicit expected behavior;
- invalid data is separated from valid operational rejection;
- manual review is treated as a valid safety outcome;
- every final decision can include a reason;
- backend and expert-system work can use these scenarios as acceptance tests;
- documentation is updated when implementation behavior changes.
