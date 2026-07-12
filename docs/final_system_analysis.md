# Final System Analysis

## 1. Project Overview

The Hybrid Intelligent Warehouse System is designed to support warehouse robot task assignment by combining machine-learning outputs with rule-based expert reasoning.

The system addresses a warehouse environment where:

- orders arrive continuously;
- shelves may be available, unavailable, or uncertain;
- robots have different battery levels, payload limits, locations, workloads, and operational states;
- warehouse load changes over time;
- robot failures or unavailable resources may require reassignment.

The solution separates prediction from decision-making:

- machine-learning components estimate future warehouse load and shelf status;
- the expert-system layer evaluates business and safety rules;
- routing and assignment components select a suitable robot and path;
- the API layer exposes the result to external clients.

---

## 2. Business Problem

A large warehouse may process thousands of orders every day. Manual robot assignment becomes inefficient because every decision may depend on several changing constraints:

- order priority;
- order weight;
- shelf location and status;
- robot payload capacity;
- robot battery level;
- robot workload;
- robot current zone;
- warehouse congestion;
- robot availability;
- route accessibility.

The system must transform these inputs into an explainable operational decision.

The expected final decision is not only:

> Assign robot R1.

It should also explain:

- why the robot is suitable;
- why other robots were rejected;
- whether manual review is required;
- whether the route is valid;
- whether reassignment is needed.

---

## 3. Project Objectives

The system has the following objectives:

1. Forecast short-term warehouse order load.
2. Analyze shelf status through a recognition interface.
3. Convert machine-learning outputs into validated expert-system facts.
4. Apply safety and business rules to robot candidates.
5. Calculate a route between the robot and the target shelf.
6. Select the most suitable robot.
7. Support replanning when the assigned robot becomes unavailable.
8. Expose the workflow through a backend API.
9. Produce explainable and testable decisions.

---

## 4. Main Actors

### 4.1 Warehouse Operator

The warehouse operator submits or reviews an order-assignment request.

Responsibilities:

- create or inspect orders;
- review manual-review warnings;
- inspect the selected robot;
- inspect the reason for the decision;
- confirm or reject exceptional cases.

### 4.2 Warehouse Management System

An external warehouse-management application may call the backend API.

Responsibilities:

- provide order information;
- request an assignment;
- receive the assignment result;
- store the operational result.

### 4.3 System Administrator

The administrator maintains technical and operational configuration.

Responsibilities:

- configure robot constraints;
- update shelf and zone data;
- monitor system health;
- review failures;
- maintain rules and model versions.

### 4.4 Robot

A robot is treated as an operational entity rather than a human actor.

It provides:

- identifier;
- battery level;
- payload capacity;
- current zone;
- workload;
- operational status.

---

## 5. System Inputs

### 5.1 Order Data

Required order information:

- `order_id`
- `priority`
- `total_weight_kg`
- `shelf_id`

The order determines the target shelf, urgency, and minimum robot capacity.

### 5.2 Robot Data

Required robot information:

- `robot_id`
- `battery_level`
- `maximum_load_kg`
- `current_zone_id`
- `current_workload`
- `status`

These values are used to reject unsuitable robots and rank valid candidates.

### 5.3 Shelf Data

Required shelf information:

- `shelf_id`
- `zone_id`
- physical or operational status

Shelf information identifies the target location and whether the order can continue automatically.

### 5.4 Forecast Data

Required forecast information:

- forecast time;
- forecast horizon;
- expected number of orders;
- warehouse load level;
- model version;
- generation timestamp.

The forecast helps the expert system adapt assignment decisions under low, medium, or high load.

### 5.5 Shelf Recognition Data

Required recognition information:

- shelf identifier;
- predicted status;
- confidence;
- model version;
- prediction timestamp;
- manual-review flag.

A low-confidence result must not be treated as a confirmed physical fact.

### 5.6 Warehouse Graph Data

Routing requires:

- warehouse zones;
- graph nodes;
- graph edges;
- edge cost or distance;
- blocked paths;
- source and destination zones.

---

## 6. System Outputs

The final assignment result should contain:

- selected robot identifier;
- selected route;
- assignment status;
- decision reason;
- rejected robot reasons;
- manual-review requirement;
- warehouse-load context;
- generated timestamp;
- relevant model and rule versions.

Possible assignment statuses include:

- assigned;
- rejected;
- manual_review;
- no_suitable_robot;
- replanning_required;
- failed.

---

## 7. Main Modules and Responsibilities

### 7.1 Mock Data Layer

Provides deterministic development data for:

- orders;
- shelves;
- robots;
- zones;
- routes;
- historical demand;
- system scenarios.

This layer allows independent implementation before production data is available.

### 7.2 Shared Schemas

Defines validated contracts between modules.

Responsibilities:

- enforce required fields;
- validate enum values;
- validate timestamps;
- reject invalid numeric values;
- standardize module communication.

### 7.3 Order Forecasting

Uses historical order data to estimate near-future demand.

Current output:

- expected order count;
- load level;
- model metadata.

The forecast does not assign robots directly. It provides context to the decision layer.

### 7.4 Shelf Recognition

Defines the interface for image-based shelf-status prediction.

Current implementation supports:

- predictor abstraction;
- image validation;
- confidence handling;
- manual-review behavior;
- fallback result when no image is available.

Because real shelf images are not currently available, the system uses an explicit `unknown` result and requires manual review rather than inventing a confident prediction.

### 7.5 ML Integration

Transforms forecasting and shelf-recognition outputs into `ExpertSystemFacts`.

Responsibilities:

- verify that the order and shelf match;
- verify that the prediction belongs to the target shelf;
- reject duplicate robots;
- require at least one robot;
- preserve timezone-aware timestamps;
- produce a validated expert-system input object.

### 7.6 Expert System

The expert system is responsible for decision rules.

Expected responsibilities:

- reject unavailable robots;
- reject robots with insufficient payload capacity;
- reject robots with insufficient battery;
- detect uncertain shelf state;
- account for high warehouse load;
- rank valid candidates;
- explain every rejection and final decision.

### 7.7 Routing

The routing module calculates a valid path through the warehouse graph.

Expected responsibilities:

- find a path from robot zone to shelf zone;
- avoid blocked edges;
- calculate route cost;
- report when no path exists.

### 7.8 Robot Assignment

Combines expert-system eligibility with route information.

Expected responsibilities:

- compare suitable robots;
- rank candidates;
- select the best robot;
- return an explainable assignment.

### 7.9 Replanning

Handles operational changes after assignment.

Expected triggers:

- robot failure;
- robot becomes unavailable;
- route becomes blocked;
- target shelf becomes unavailable;
- assignment timeout.

### 7.10 Backend API

Provides external access to the system.

Expected responsibilities:

- request validation;
- assignment endpoints;
- system health endpoint;
- error handling;
- response serialization;
- integration with database and services.

### 7.11 Database

Stores operational and historical information.

Expected entities:

- orders;
- robots;
- shelves;
- assignments;
- routes;
- model results;
- decision logs;
- failure events.

---

## 8. Functional Requirements

The system shall:

1. validate incoming order data;
2. load or receive current robot states;
3. identify the order target shelf;
4. generate or receive a demand forecast;
5. generate or receive a shelf-status prediction;
6. convert ML outputs into expert-system facts;
7. reject invalid or unsafe robot candidates;
8. calculate routes for suitable candidates;
9. select a robot using defined ranking rules;
10. return an explainable result;
11. store the assignment result;
12. support reassignment after failure;
13. expose system health information;
14. preserve timestamps and version information;
15. support automated tests.

---

## 9. Non-Functional Requirements

### 9.1 Explainability

Every decision must include a reason.

The system should distinguish between:

- robot rejected because of payload;
- robot rejected because of battery;
- robot rejected because of status;
- order blocked because of shelf uncertainty;
- assignment rejected because no route exists.

### 9.2 Reliability

The system must not silently accept invalid data.

Examples:

- duplicate robot identifiers;
- missing shelf;
- mismatched shelf prediction;
- timezone-naive timestamps;
- unsupported enum values.

### 9.3 Modularity

Each module should communicate through schemas rather than direct internal assumptions.

### 9.4 Testability

Core business behavior should be covered by:

- unit tests;
- schema-validation tests;
- integration tests;
- end-to-end demonstration scripts.

### 9.5 Extensibility

The system should allow replacement of:

- the forecasting model;
- the shelf-recognition model;
- the routing algorithm;
- the expert-rule implementation;
- the database backend.

### 9.6 Safety

Uncertain shelf status or unsafe robot conditions must not result in automatic assignment.

---

## 10. Main Business Rules

The final expert-system implementation should include at least the following rules.

### Rule 1: Robot Availability

A robot can be considered only if its operational status allows assignment.

### Rule 2: Payload Capacity

A robot must have:

```text
maximum_load_kg >= order.total_weight_kg
```

### Rule 3: Battery Safety

A robot with battery below the configured safety threshold must be rejected.

### Rule 4: Shelf Confidence

If shelf confidence is below the accepted threshold, the result requires manual review.

### Rule 5: Shelf Availability

An unavailable shelf blocks automatic assignment.

### Rule 6: Workload

Robots with lower current workload should generally be preferred when other conditions are similar.

### Rule 7: Route Availability

A robot cannot be assigned if no valid route exists.

### Rule 8: Order Priority

Higher-priority orders should receive preference when warehouse capacity is constrained.

### Rule 9: High Warehouse Load

Under high load, the system may apply stricter workload and routing rules.

### Rule 10: Replanning

If the selected robot fails, the system must exclude it and evaluate remaining candidates.

---

## 11. Normal Workflow

1. An order is received.
2. The order schema validates the input.
3. Current robot and shelf states are loaded.
4. The forecasting service estimates near-future load.
5. The shelf-recognition service returns a prediction or fallback.
6. ML integration builds `ExpertSystemFacts`.
7. The expert system filters robot candidates.
8. Routing calculates paths for valid robots.
9. Assignment ranks candidates.
10. The selected assignment is returned.
11. The result is stored and logged.

---

## 12. Exceptional Workflows

### 12.1 Shelf Requires Manual Review

The system returns a manual-review result and avoids automatic assignment.

### 12.2 No Suitable Robot

The system returns `no_suitable_robot` and includes rejection reasons.

### 12.3 No Route

The robot is rejected even if its capacity and battery are valid.

### 12.4 Robot Failure

The replanning module excludes the failed robot and starts candidate evaluation again.

### 12.5 Invalid ML Output

The integration layer rejects malformed or inconsistent model output.

### 12.6 Forecasting Failure

The system should use a defined fallback policy, such as a default load level, while recording the failure.

---

## 13. Current Implementation Status

### Implemented

- project structure;
- mock datasets;
- shared schemas;
- forecasting pipeline;
- forecasting evaluation;
- shelf-recognition interface;
- shelf-recognition fallback;
- ML integration;
- ML end-to-end demonstration;
- CI workflow;
- automated tests.

### Partially Implemented

- shelf recognition, because no real image dataset is available;
- end-to-end workflow, because the expert system, routing, assignment, database, and backend are not yet connected.

### Not Yet Implemented

- complete expert-system rules;
- routing algorithm;
- robot-ranking algorithm;
- replanning;
- database persistence;
- backend API.

---

## 14. Assumptions

The current project assumes:

- robot state is available when assignment starts;
- every order references one target shelf;
- warehouse routes can be represented as a graph;
- order weight is known;
- shelf and robot identifiers are unique;
- timestamps use timezone-aware values;
- mock data represents development scenarios, not production volume;
- the forecasting horizon is short-term;
- low-confidence recognition must trigger manual review.

---

## 15. Limitations

Current limitations:

- historical data is synthetic;
- no production database is connected;
- no real shelf-image dataset is available;
- the shelf-recognition model is not trained;
- the expert-system engine is not complete;
- routes are mock graph data;
- the backend API is not complete;
- the current demo stops at validated expert-system facts;
- no real robot hardware is connected.

These limitations should be presented honestly. They do not invalidate the architecture, but they define the difference between the current prototype and a production system.

---

## 16. Acceptance Criteria

The project can be considered functionally complete when:

1. valid orders produce assignment decisions;
2. unsafe robots are rejected;
3. rejection reasons are returned;
4. shelf uncertainty triggers manual review;
5. routing returns a valid path or clear failure;
6. the best suitable robot is selected;
7. robot failure triggers reassignment;
8. API requests and responses are validated;
9. decisions are stored;
10. all automated tests pass;
11. the complete scenario runs through one command or API call;
12. documentation matches the implemented behavior.

---

## 17. Definition of Done for the System Analyst / Data Scientist Role

The System Analyst / Data Scientist contribution is complete when:

- system requirements are documented;
- module responsibilities are defined;
- ML contracts are stable;
- forecasting is evaluated;
- shelf-recognition limitations are documented;
- ML outputs are integrated with expert-system facts;
- edge cases and scenarios are defined;
- integration tests validate the ML workflow;
- the final presentation accurately explains implemented and simulated parts.
