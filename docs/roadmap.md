# Project Roadmap

## Document Information

| Field | Value |
|---|---|
| Project name | Hybrid Intelligent Warehouse System |
| Document version | 0.1 |
| Document type | Implementation Roadmap |
| Team | Abdelrahman and Halit |
| Current phase | MVP implementation planning |

## 1. Purpose

This document defines the implementation plan for the Hybrid Intelligent Warehouse System.

The roadmap specifies:

- project phases;
- task ownership;
- implementation order;
- dependencies between tasks;
- expected deliverables;
- MVP completion criteria;
- testing and integration activities.

The roadmap focuses on completing a working and demonstrable MVP.

## 2. Team Roles

### 2.1 Abdelrahman

Primary role:

```text
System Analyst / Data Scientist
```

Main responsibilities:

- system analysis;
- project requirements;
- architecture documentation;
- data contracts;
- data dictionary;
- mock data preparation;
- order forecasting;
- shelf recognition;
- machine-learning model evaluation;
- ML integration support;
- documentation review;
- final report preparation.

### 2.2 Halit

Primary role:

```text
Backend / Expert System Developer
```

Main responsibilities:

- FastAPI backend;
- PostgreSQL database;
- database models;
- expert-system implementation;
- external rule loading;
- route planning;
- robot ranking;
- assignment logic;
- replanning logic;
- API integration;
- backend testing.

### 2.3 Shared Responsibilities

Both participants are responsible for:

- reviewing data contracts;
- resolving integration issues;
- testing the complete workflow;
- maintaining Git history;
- updating documentation;
- preparing the final demonstration;
- reviewing the final report.

## 3. MVP Scope

The MVP must demonstrate the following workflow:

```text
Create warehouse order
        ↓
Load warehouse and robot data
        ↓
Generate workload forecast
        ↓
Predict shelf status
        ↓
Convert information into facts
        ↓
Evaluate expert-system rules
        ↓
Filter unsuitable robots
        ↓
Calculate routes
        ↓
Rank eligible robots
        ↓
Select the best robot
        ↓
Store the assignment and explanation
        ↓
Return the final decision through the API
```

The MVP must also demonstrate replanning when an assigned robot fails.

## 4. Implementation Principles

The project shall follow these principles:

1. complete the simplest working workflow first;
2. use mock outputs before real ML models are ready;
3. keep modules independently testable;
4. avoid microservices during the MVP;
5. prioritize integration over unnecessary complexity;
6. store important decisions and explanations;
7. keep ML training separate from runtime prediction;
8. keep expert-system rules outside the source code;
9. update documentation when contracts change;
10. maintain a working main branch.

## 5. Phase Overview

| Phase | Name | Main result |
|---|---|---|
| Phase 0 | Project Foundation | Repository and documentation ready |
| Phase 1 | Mock Data and Core Models | Test data and shared schemas available |
| Phase 2 | Backend and Database | API and persistence layer operational |
| Phase 3 | Forecasting Module | Workload forecast available |
| Phase 4 | Shelf Recognition Module | Shelf prediction available |
| Phase 5 | Expert System | Robot eligibility decisions available |
| Phase 6 | Routing and Ranking | Robot selection available |
| Phase 7 | Integration | End-to-end assignment workflow operational |
| Phase 8 | Replanning | Robot-failure recovery operational |
| Phase 9 | Testing and Documentation | MVP validated and documented |
| Phase 10 | Final Demonstration | Project ready for submission |

## 6. Phase 0: Project Foundation

### Objective

Prepare the repository, documentation, and module structure.

### Tasks

| ID | Task | Owner | Status |
|---|---|---|---|
| P0-01 | Create repository structure | Shared | Completed |
| P0-02 | Create README | Shared | Completed |
| P0-03 | Define project scope | Abdelrahman | Completed |
| P0-04 | Define system requirements | Abdelrahman | Completed |
| P0-05 | Define architecture | Abdelrahman | Completed |
| P0-06 | Define data contracts | Abdelrahman | Completed |
| P0-07 | Define data dictionary | Abdelrahman | Completed |
| P0-08 | Define project roadmap | Abdelrahman | In progress |
| P0-09 | Initialize Git repository | Shared | Pending |
| P0-10 | Create first Git commit | Shared | Pending |

### Deliverables

```text
README.md
docs/project_scope.md
docs/requirements.md
docs/architecture.md
docs/data_contracts.md
docs/data_dictionary.md
docs/roadmap.md
```

### Completion Criteria

- all main documentation files exist;
- repository structure matches the architecture;
- responsibilities are assigned;
- initial contracts are available.

## 7. Phase 1: Mock Data and Shared Schemas

### Objective

Prepare test data and validated Python objects before implementing the complete system.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P1-01 | Create mock products | Halit | P0 |
| P1-02 | Create mock shelves | Halit | P0 |
| P1-03 | Create mock zones and paths | Halit | P0 |
| P1-04 | Create mock robots | Halit | P0 |
| P1-05 | Create mock orders | Shared | P0 |
| P1-06 | Create mock historical order data | Abdelrahman | P0 |
| P1-07 | Create sample shelf images or image references | Abdelrahman | P0 |
| P1-08 | Create Pydantic models for shared contracts | Halit | P0 |
| P1-09 | Validate mock files against contracts | Shared | P1-01 to P1-08 |

### Planned Files

```text
data/mock/orders.json
data/mock/robots.json
data/mock/products.json
data/mock/shelves.json
data/mock/zones.json
data/mock/warehouse_paths.json
data/mock/historical_orders.csv
data/mock/shelf_images/
```

### Completion Criteria

- at least one valid complete test scenario exists;
- at least one rejected assignment scenario exists;
- at least one robot-failure scenario exists;
- all mock data follows the data contracts.

## 8. Phase 2: Backend and Database

### Objective

Create the FastAPI application and PostgreSQL persistence layer.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P2-01 | Create FastAPI application entry point | Halit | P0 |
| P2-02 | Create environment configuration | Halit | P0 |
| P2-03 | Configure PostgreSQL connection | Halit | P0 |
| P2-04 | Create SQLAlchemy models | Halit | P1 |
| P2-05 | Create database migrations | Halit | P2-04 |
| P2-06 | Create repositories or database services | Halit | P2-04 |
| P2-07 | Add health-check endpoint | Halit | P2-01 |
| P2-08 | Add API error handling | Halit | P2-01 |
| P2-09 | Create seed script for mock data | Halit | P1, P2-04 |

### Minimum API Endpoints

```text
GET  /health
POST /orders
GET  /orders/{order_id}
GET  /robots
PATCH /robots/{robot_id}/status
POST /assignments/plan
GET  /decisions/{decision_id}
POST /rules/reload
```

### Completion Criteria

- application starts successfully;
- database connection works;
- migrations run successfully;
- seed data can be inserted;
- health endpoint returns a successful response.

## 9. Phase 3: Order Forecasting Module

### Objective

Predict the number of warehouse orders expected during the next hour.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P3-01 | Explore historical order data | Abdelrahman | P1-06 |
| P3-02 | Define forecasting features | Abdelrahman | P3-01 |
| P3-03 | Create baseline forecasting method | Abdelrahman | P3-02 |
| P3-04 | Train forecasting model | Abdelrahman | P3-03 |
| P3-05 | Evaluate model performance | Abdelrahman | P3-04 |
| P3-06 | Save model artifact | Abdelrahman | P3-04 |
| P3-07 | Implement runtime prediction service | Abdelrahman | P3-06 |
| P3-08 | Implement load-level classification | Abdelrahman | P3-07 |
| P3-09 | Add unit tests | Abdelrahman | P3-07 |
| P3-10 | Provide mock fallback | Abdelrahman | P3-07 |

### Initial Model Options

The MVP may use one of:

```text
Moving Average
Linear Regression
Random Forest Regressor
Gradient Boosting Regressor
```

The simplest model that produces valid and explainable results should be preferred.

### Suggested Evaluation Metrics

```text
MAE
RMSE
```

### Completion Criteria

- module accepts historical or prepared features;
- module returns the Forecast Result Contract;
- output includes expected orders and load level;
- model artifact can be loaded during runtime;
- mock fallback works when the artifact is unavailable.

## 10. Phase 4: Shelf Recognition Module

### Objective

Classify the condition of a warehouse shelf from an image.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P4-01 | Prepare shelf image dataset | Abdelrahman | P1-07 |
| P4-02 | Define image classes | Abdelrahman | P4-01 |
| P4-03 | Create image preprocessing pipeline | Abdelrahman | P4-01 |
| P4-04 | Train baseline classification model | Abdelrahman | P4-03 |
| P4-05 | Evaluate model accuracy | Abdelrahman | P4-04 |
| P4-06 | Save model and class mapping | Abdelrahman | P4-04 |
| P4-07 | Implement runtime prediction service | Abdelrahman | P4-06 |
| P4-08 | Implement confidence handling | Abdelrahman | P4-07 |
| P4-09 | Implement manual-review threshold | Abdelrahman | P4-08 |
| P4-10 | Add unit tests | Abdelrahman | P4-07 |
| P4-11 | Provide mock fallback | Abdelrahman | P4-07 |

### Supported Classes

```text
empty
low_stock
normal
full
unknown
```

### Initial Confidence Threshold

```text
0.60
```

### Completion Criteria

- module accepts a valid shelf image;
- module returns the Shelf Recognition Result Contract;
- low-confidence predictions trigger manual review;
- invalid images return structured errors;
- mock fallback is available.

## 11. Phase 5: Expert System

### Objective

Apply logical rules to determine robot eligibility and warehouse constraints.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P5-01 | Define VSO entities and relations | Halit | P0 |
| P5-02 | Define rule-file format | Halit | P0 |
| P5-03 | Implement rule loader | Halit | P5-02 |
| P5-04 | Implement rule validation | Halit | P5-03 |
| P5-05 | Implement fact representation | Halit | P1-08 |
| P5-06 | Implement rule evaluation engine | Halit | P5-03, P5-05 |
| P5-07 | Implement rejection reasoning | Halit | P5-06 |
| P5-08 | Record applied rules | Halit | P5-06 |
| P5-09 | Implement rule reload | Halit | P5-03 |
| P5-10 | Add expert-system unit tests | Halit | P5-06 |

### Minimum Rules

The MVP should include rules for:

```text
robot availability
minimum battery level
maximum load capacity
robot failure status
shelf empty status
manual-review requirement
product availability
inactive warehouse zone
unavailable route
```

### Completion Criteria

- expert system accepts structured facts;
- unsuitable robots are rejected;
- rejection reasons are returned;
- applied rule identifiers are recorded;
- rules can be changed outside the source code.

## 12. Phase 6: Routing and Robot Ranking

### Objective

Calculate routes and choose the best eligible robot.

### 12.1 Route Planning Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P6-01 | Build warehouse graph representation | Halit | P1-03 |
| P6-02 | Implement shortest-path algorithm | Halit | P6-01 |
| P6-03 | Calculate route distance | Halit | P6-02 |
| P6-04 | Estimate travel time | Halit | P6-02 |
| P6-05 | Handle unavailable routes | Halit | P6-02 |
| P6-06 | Add route-planning tests | Halit | P6-02 |

### 12.2 Robot Ranking Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P6-07 | Define ranking formula | Halit | P0 |
| P6-08 | Implement battery score | Halit | P6-07 |
| P6-09 | Implement distance score | Halit | P6-07 |
| P6-10 | Implement workload score | Halit | P6-07 |
| P6-11 | Implement priority score | Halit | P6-07 |
| P6-12 | Implement deterministic tie-breaking | Halit | P6-07 |
| P6-13 | Return score breakdown | Halit | P6-08 to P6-12 |
| P6-14 | Add ranking tests | Halit | P6-13 |

### Initial Ranking Factors

```text
battery level
route distance
estimated travel time
current workload
order priority
```

### Completion Criteria

- routes are generated for eligible robots;
- unavailable routes are excluded;
- candidates receive numeric scores;
- candidates are ranked deterministically;
- score components are included in the result.

## 13. Phase 7: System Integration

### Objective

Connect all modules into one assignment workflow.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P7-01 | Implement orchestration service | Shared | P2 to P6 |
| P7-02 | Load order and warehouse data | Halit | P2 |
| P7-03 | Call forecasting module | Abdelrahman | P3 |
| P7-04 | Call shelf-recognition module | Abdelrahman | P4 |
| P7-05 | Build expert-system facts | Shared | P3, P4, P5 |
| P7-06 | Call expert system | Halit | P5 |
| P7-07 | Call route planning | Halit | P6 |
| P7-08 | Call robot ranking | Halit | P6 |
| P7-09 | Build final decision | Shared | P7-03 to P7-08 |
| P7-10 | Store decision and assignment | Halit | P2, P7-09 |
| P7-11 | Expose assignment endpoint | Halit | P7-01 |
| P7-12 | Add integration tests | Shared | P7-01 to P7-11 |

### Completion Criteria

A request to:

```text
POST /assignments/plan
```

must return either:

```text
assigned
rejected
manual_review_required
```

The response must include an explanation.

## 14. Phase 8: Failure and Replanning

### Objective

Reassign an order when the selected robot fails.

### Tasks

| ID | Task | Owner | Depends on |
|---|---|---|---|
| P8-01 | Implement robot status update | Halit | P2 |
| P8-02 | Detect failure during active assignment | Halit | P8-01 |
| P8-03 | Mark current assignment as failed | Halit | P8-02 |
| P8-04 | Exclude failed robot | Halit | P8-02 |
| P8-05 | Repeat expert evaluation | Halit | P5 |
| P8-06 | Recalculate routes | Halit | P6 |
| P8-07 | Repeat ranking | Halit | P6 |
| P8-08 | Create replacement assignment | Halit | P8-05 to P8-07 |
| P8-09 | Store replanning explanation | Shared | P8-08 |
| P8-10 | Add replanning integration test | Shared | P8-01 to P8-09 |

### Completion Criteria

- failed robot is excluded;
- original assignment is preserved in history;
- replacement robot is selected when available;
- failure is explained when reassignment is impossible.

## 15. Phase 9: Testing and Quality Review

### Objective

Verify module behavior and the complete workflow.

### 15.1 Unit Testing

Required unit-test areas:

```text
forecast preprocessing
forecast prediction
load-level classification
image preprocessing
shelf prediction
confidence threshold
rule validation
rule evaluation
route calculation
robot ranking
tie-breaking
data validation
```

### 15.2 Integration Testing

Required integration scenarios:

1. successful assignment;
2. no eligible robot;
3. robot battery below threshold;
4. robot load capacity too low;
5. shelf is empty;
6. shelf prediction requires manual review;
7. no route is available;
8. assigned robot fails;
9. reassignment succeeds;
10. reassignment fails.

### 15.3 Quality Tasks

| ID | Task | Owner |
|---|---|---|
| P9-01 | Run code formatter | Shared |
| P9-02 | Run linter | Shared |
| P9-03 | Run type checker if configured | Shared |
| P9-04 | Run unit tests | Shared |
| P9-05 | Run integration tests | Shared |
| P9-06 | Review API documentation | Shared |
| P9-07 | Review data contracts | Shared |
| P9-08 | Review database migrations | Halit |
| P9-09 | Review ML artifacts | Abdelrahman |
| P9-10 | Remove unused code and files | Shared |

### Completion Criteria

- tests pass;
- API starts without errors;
- complete workflow produces repeatable output;
- documentation matches the implementation;
- no credentials or generated secrets are committed.

## 16. Phase 10: Packaging and Final Demonstration

### Objective

Prepare the project for review and presentation.

### Tasks

| ID | Task | Owner |
|---|---|---|
| P10-01 | Create Dockerfile | Halit |
| P10-02 | Create Docker Compose configuration | Halit |
| P10-03 | Verify local Python execution | Shared |
| P10-04 | Verify Docker execution | Shared |
| P10-05 | Update README setup instructions | Abdelrahman |
| P10-06 | Add example API requests | Abdelrahman |
| P10-07 | Prepare demonstration data | Shared |
| P10-08 | Prepare demonstration scenario | Shared |
| P10-09 | Prepare final report | Abdelrahman |
| P10-10 | Prepare presentation materials | Shared |
| P10-11 | Create final release tag | Shared |

### Demonstration Scenario

The final demonstration should show:

1. application startup;
2. seeded warehouse data;
3. order creation;
4. forecast generation;
5. shelf prediction;
6. expert-system evaluation;
7. route calculation;
8. robot ranking;
9. final assignment;
10. decision explanation;
11. robot failure;
12. successful replanning.

## 17. Priority Classification

### 17.1 Must Have

The following tasks are required for the MVP:

```text
repository structure
documentation
mock warehouse data
FastAPI application
PostgreSQL database
order creation
robot data
forecast output
shelf prediction output
expert-system rules
robot filtering
route planning
robot ranking
final assignment response
decision explanation
basic tests
```

### 17.2 Should Have

The following tasks should be completed when time allows:

```text
real trained forecasting model
real shelf image classifier
database migrations
rule reload endpoint
robot failure replanning
Docker execution
score breakdown
model metadata
```

### 17.3 Could Have

The following tasks are optional:

```text
web dashboard
live robot communication
advanced computer vision
deep-learning forecasting
real-time event broker
multiple warehouses
authentication and authorization
interactive warehouse map
```

### 17.4 Excluded from MVP

The following items are excluded:

```text
microservices
Kubernetes
Kafka
real autonomous robot control
production cloud deployment
real-time camera streaming
large-scale distributed processing
```

## 18. Dependency Summary

The major dependency order is:

```text
Documentation
        ↓
Data Contracts and Mock Data
        ↓
Shared Pydantic Models
        ↓
Backend and Database
        ↓
Forecasting and Shelf Recognition
        ↓
Expert System
        ↓
Routing and Ranking
        ↓
Orchestration
        ↓
Replanning
        ↓
Testing
        ↓
Final Demonstration
```

Machine-learning development and backend development may proceed in parallel after the data contracts are agreed.

## 19. Risk Management

| Risk | Impact | Mitigation |
|---|---|---|
| ML dataset is insufficient | Models may perform poorly | Use simple baseline and mock fallback |
| Module outputs do not match | Integration failure | Validate all outputs using Pydantic |
| Expert rules become inconsistent | Incorrect decisions | Add rule validation and tests |
| PostgreSQL setup delays progress | Backend delay | Use mock repositories temporarily |
| Route graph is incomplete | Assignment failure | Provide complete mock warehouse graph |
| Project scope becomes too large | MVP not completed | Prioritize Must Have tasks |
| Team tasks overlap | Duplicate or conflicting work | Follow ownership table |
| Changes break contracts | Integration regressions | Review and version contracts |
| Docker configuration consumes time | Delayed core features | Complete local execution first |
| Final integration happens too late | Major unresolved defects | Integrate mock modules early |

## 20. Git Workflow

The team should use the following branch strategy:

```text
main
develop
feature/<task-name>
```

Examples:

```text
feature/order-forecasting
feature/shelf-recognition
feature/expert-system
feature/database-models
feature/robot-ranking
```

Rules:

1. `main` must contain stable code;
2. feature work should use separate branches;
3. commits should be small and descriptive;
4. pull requests should be reviewed by the other participant;
5. data-contract changes require both participants' approval;
6. generated files and local secrets must not be committed.

## 21. Commit Message Convention

Recommended commit prefixes:

```text
docs:
feat:
fix:
test:
refactor:
build:
chore:
```

Examples:

```text
docs: add system architecture
feat: implement forecast result model
feat: add expert rule loader
test: add robot ranking tests
fix: handle unavailable warehouse route
```

## 22. Definition of Done

A task is complete when:

- implementation is finished;
- code follows project structure;
- inputs and outputs follow the contracts;
- validation is included;
- errors are handled;
- tests are added when applicable;
- documentation is updated;
- the task is reviewed;
- the code works with the current integrated application.

## 23. MVP Completion Checklist

The MVP is complete when:

- [ ] the application starts successfully;
- [ ] PostgreSQL is connected;
- [ ] mock data can be loaded;
- [ ] orders can be created;
- [ ] forecasting returns a valid result;
- [ ] shelf recognition returns a valid result;
- [ ] expert rules filter robots;
- [ ] routes are calculated;
- [ ] eligible robots are ranked;
- [ ] one robot is selected;
- [ ] decisions are stored;
- [ ] explanations are returned;
- [ ] failed robots can be excluded;
- [ ] tests pass;
- [ ] README instructions work;
- [ ] the final demonstration is repeatable.

## 24. Current Status

Current project status:

```text
Documentation and planning in progress
```

Completed:

```text
repository structure
README
project scope
requirements
architecture
data contracts
data dictionary
```

Next immediate tasks:

```text
initialize Git
create mock data
create shared Pydantic schemas
start FastAPI application
```

## 25. Approval Status

This roadmap version is currently:

```text
Proposed
```

It becomes:

```text
Approved
```

after review by Abdelrahman and Halit.