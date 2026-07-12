# System Flow

## 1. High-Level Flow

```mermaid
flowchart LR
    A[Order Request] --> B[Input Validation]
    B --> C[Load Order, Shelf, and Robot State]
    C --> D[Order Forecasting]
    C --> E[Shelf Recognition]
    D --> F[ML Integration]
    E --> F
    C --> F
    F --> G[Expert System]
    G --> H[Routing]
    H --> I[Robot Assignment]
    I --> J[Persist Decision]
    J --> K[API Response]
```

---

## 2. ML-to-Decision Flow

```mermaid
flowchart TD
    A[Historical Orders] --> B[Forecasting Model]
    B --> C[ForecastResult]

    D[Shelf Image or Fallback] --> E[Shelf Recognition Service]
    E --> F[ShelfPredictionResult]

    G[Order]
    H[Robots]
    I[Shelf]

    C --> J[ML Integration Service]
    F --> J
    G --> J
    H --> J
    I --> J

    J --> K[ExpertSystemFacts]
    K --> L[Expert Rules]
    L --> M[Eligible Robots]
    L --> N[Rejected Robots and Reasons]
```

---

## 3. Robot Selection Flow

```mermaid
flowchart TD
    A[Candidate Robots] --> B{Robot Available?}
    B -- No --> X[Reject: unavailable]
    B -- Yes --> C{Capacity Sufficient?}
    C -- No --> Y[Reject: insufficient payload]
    C -- Yes --> D{Battery Safe?}
    D -- No --> Z[Reject: low battery]
    D -- Yes --> E{Shelf Confirmed?}
    E -- No --> M[Manual Review]
    E -- Yes --> F{Route Available?}
    F -- No --> R[Reject: no route]
    F -- Yes --> G[Calculate Candidate Score]
    G --> H[Rank Valid Robots]
    H --> I[Select Best Robot]
```

---

## 4. Replanning Flow

```mermaid
flowchart TD
    A[Active Assignment] --> B{Failure Event?}
    B -- No --> C[Continue Assignment]
    B -- Yes --> D[Mark Current Robot Unavailable]
    D --> E[Exclude Failed Robot]
    E --> F[Reload Current Robot States]
    F --> G[Run Expert Rules Again]
    G --> H[Recalculate Routes]
    H --> I{Alternative Robot Found?}
    I -- Yes --> J[Create Replacement Assignment]
    I -- No --> K[Escalate to Operator]
```

---

## 5. Current Implemented Flow

The current implementation reaches the following point:

```mermaid
flowchart LR
    A[Mock Order] --> B[Forecasting]
    A --> C[Shelf Fallback]
    B --> D[ML Integration]
    C --> D
    E[Mock Robots and Shelf] --> D
    D --> F[Validated ExpertSystemFacts]
    F --> G[JSON Demo Report]
```

The following modules are still expected after this point:

```text
ExpertSystemFacts
→ Expert System
→ Routing
→ Robot Assignment
→ Database
→ API Response
```

---

## 6. Main Data Contracts

### Forecasting Output

```text
ForecastResult
├── forecast_time
├── forecast_horizon_minutes
├── expected_orders
├── load_level
├── model_version
└── generated_at
```

### Shelf Recognition Output

```text
ShelfPredictionResult
├── shelf_id
├── status
├── confidence
├── model_version
├── prediction_time
└── requires_manual_review
```

### Expert-System Input

```text
ExpertSystemFacts
├── order
│   ├── order_id
│   ├── priority
│   ├── total_weight_kg
│   └── shelf_id
├── robots[]
│   ├── robot_id
│   ├── battery_level
│   ├── maximum_load_kg
│   ├── current_zone_id
│   ├── current_workload
│   └── status
├── shelf
│   ├── shelf_id
│   ├── zone_id
│   ├── status
│   ├── confidence
│   └── requires_manual_review
├── forecast
│   ├── expected_orders
│   └── load_level
└── generated_at
```

---

## 7. Module Ownership

### System Analyst / Data Scientist

- requirements;
- data contracts;
- mock scenarios;
- forecasting;
- shelf-recognition interface;
- ML evaluation;
- ML integration;
- limitations;
- end-to-end ML validation.

### Backend / Expert-System Developer

- FastAPI backend;
- database;
- expert-system rules;
- routing;
- assignment;
- replanning;
- persistence;
- operational API responses.

### Shared Responsibilities

- integration;
- end-to-end tests;
- final demo;
- documentation review;
- presentation;
- defense preparation.
