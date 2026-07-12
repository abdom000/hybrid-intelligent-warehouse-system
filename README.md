# Hybrid Intelligent Warehouse System

[![CI](https://github.com/abdom000/hybrid-intelligent-warehouse-system/actions/workflows/ci.yml/badge.svg)](https://github.com/abdom000/hybrid-intelligent-warehouse-system/actions/workflows/ci.yml)

A modular educational prototype for intelligent warehouse operations that combines short-term order forecasting, shelf-status recognition, validated ML-to-expert-system contracts, rule-based reasoning, route planning, and robot assignment.

## Project Overview

Large warehouses process many orders while robot assignment depends on several changing conditions:

- order priority and weight;
- shelf location and operational state;
- robot availability, battery level, payload capacity, and workload;
- predicted warehouse load;
- route availability;
- operational failures that may require reassignment.

The project separates **prediction** from **decision-making**:

```text
Historical orders ──→ Order forecasting ──┐
                                         │
Shelf image/fallback ─→ Shelf recognition ├─→ ML integration
                                         │
Order + robots + shelf state ─────────────┘
                                                   ↓
                                         Expert-system facts
                                                   ↓
                                  Rules → routing → assignment
                                                   ↓
                                    Decision and explanation
```

The current repository contains a complete System Analyst / Data Scientist foundation and an ML integration workflow. The expert-system, routing, assignment, database, and backend layers remain separate implementation workstreams.

## Current Status

### Implemented

- project structure and technical documentation;
- deterministic mock warehouse data;
- shared Pydantic schemas and validation;
- short-term order forecasting pipeline;
- forecasting evaluation and baseline comparison;
- shelf-recognition interface and image validation;
- safe no-image fallback with manual review;
- ML output transformation into `ExpertSystemFacts`;
- ML end-to-end demonstration;
- system scenarios and boundary tests;
- GitHub Actions CI;
- automated unit and integration tests.

### Partially Implemented

- **Shelf recognition:** the architecture, predictor interface, validation, confidence policy, and fallback are implemented, but no real image dataset is available for training a neural model.
- **End-to-end warehouse decision flow:** the current demo reaches validated expert-system facts. Final rule inference, routing, assignment, persistence, and API orchestration are not yet connected.

### Remaining Core Modules

- expert-system rules and explainable inference;
- warehouse route planning;
- robot ranking and assignment;
- failure-triggered replanning;
- database persistence;
- backend API and final orchestration.

## Implemented ML Workflow

The current executable ML demo performs:

```text
Mock order
→ forecasting
→ shelf-recognition fallback
→ ML integration
→ validated ExpertSystemFacts
→ JSON report
```

Example result:

```text
Order: O101
Forecasted orders: 24
Forecast load: low
Shelf status: unknown
Manual review required: true
Robots passed to expert system: 5
```

The `unknown` shelf status is deliberate. Without a usable image, the system does not invent a confident prediction and instead requires manual review.

## Forecasting Evaluation

The forecasting pipeline was evaluated chronologically on the synthetic historical dataset.

| Metric | Result |
|---|---:|
| Training rows | 249 |
| Test rows | 63 |
| MAE | 10.0750 |
| RMSE | 13.7329 |
| R² | 0.9133 |
| Baseline MAE | 16.3492 |
| MAE improvement over baseline | 38.38% |

These results demonstrate the development pipeline on synthetic data. They are not production-accuracy claims.

## Main Modules

### Order Forecasting

Located in:

```text
src/hybrid_warehouse/forecasting/
```

Responsibilities:

- load and validate historical order data;
- construct forecasting features;
- train and evaluate the regression model;
- generate `ForecastResult`;
- classify expected load as `low`, `medium`, or `high`.

### Shelf Recognition

Located in:

```text
src/hybrid_warehouse/shelf_recognition/
```

Responsibilities:

- validate image inputs;
- expose a replaceable predictor interface;
- return `ShelfPredictionResult`;
- enforce confidence and manual-review behavior;
- provide a safe fallback when no image is available.

Supported statuses:

```text
empty
low_stock
normal
full
unknown
```

### ML Integration

Located in:

```text
src/hybrid_warehouse/integration/
```

Responsibilities:

- verify order, shelf, and prediction identifiers;
- reject duplicate robot candidates;
- require at least one robot;
- preserve timezone-aware timestamps;
- convert ML outputs and warehouse entities into `ExpertSystemFacts`;
- run the current ML end-to-end demonstration.

### Shared Schemas

Located in:

```text
src/hybrid_warehouse/schemas/
```

Main contracts:

- `Order`
- `Robot`
- `Shelf`
- `ForecastResult`
- `ShelfPredictionResult`
- `OrderFacts`
- `RobotFacts`
- `ShelfFacts`
- `ForecastFacts`
- `ExpertSystemFacts`

### Planned Decision Modules

The following directories define the remaining decision pipeline:

```text
src/hybrid_warehouse/expert_system/
src/hybrid_warehouse/routing/
src/hybrid_warehouse/assignment/
src/hybrid_warehouse/backend/
src/hybrid_warehouse/database/
```

## Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   ├── mock/
│   ├── processed/
│   └── raw/
├── docs/
│   ├── decisions/
│   ├── architecture.md
│   ├── data_contracts.md
│   ├── data_dictionary.md
│   ├── final_system_analysis.md
│   ├── ml_contracts_final.md
│   ├── ml_evaluation.md
│   ├── project_scope.md
│   ├── requirements.md
│   ├── roadmap.md
│   ├── system_flow.md
│   └── system_scenarios.md
├── notebooks/
│   ├── forecasting/
│   └── shelf_recognition/
├── scripts/
├── src/
│   └── hybrid_warehouse/
│       ├── assignment/
│       ├── backend/
│       ├── database/
│       ├── expert_system/
│       ├── forecasting/
│       ├── integration/
│       ├── routing/
│       ├── schemas/
│       └── shelf_recognition/
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Installation

Python 3.11 is recommended.

```bash
git clone git@github.com:abdom000/hybrid-intelligent-warehouse-system.git
cd hybrid-intelligent-warehouse-system

python3.11 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Validation and Tests

Run the complete test suite:

```bash
pytest
```

Run individual validation scripts:

```bash
python scripts/validate_mock_data.py
python scripts/validate_schemas.py
python scripts/validate_shelf_recognition.py
python scripts/validate_ml_integration.py
python scripts/run_ml_end_to_end_demo.py
```

Run forecasting training and evaluation:

```bash
python scripts/train_forecasting_model.py
python scripts/evaluate_forecasting_model.py
```

Generated reports are written to:

```text
data/processed/
```

## Key System Scenarios

The documented scenarios include:

- normal order;
- high-priority order;
- heavy order;
- low-battery robot;
- unavailable robot;
- unknown shelf state;
- low-confidence shelf prediction;
- mismatched shelf prediction;
- empty robot candidate list;
- duplicate robot identifiers;
- high warehouse load;
- no suitable robot;
- unavailable route;
- robot failure and replanning;
- invalid forecasting output;
- invalid or unavailable shelf image.

See:

```text
docs/system_scenarios.md
```

## Team

### Abdelrahman — System Analyst / Data Scientist

Responsibilities:

- requirements and scope analysis;
- system and data analysis;
- mock-data design;
- shared ML contracts;
- order forecasting;
- forecasting evaluation;
- shelf-recognition architecture;
- ML integration;
- system scenarios;
- Data Science documentation.

### Halit — Backend / Expert-System Developer

Responsibilities:

- backend development;
- database integration;
- expert-system knowledge base;
- logical rules and inference;
- route planning;
- robot assignment;
- replanning;
- API integration.

## Development Workflow

The project uses a branch-and-pull-request workflow:

1. create a branch for one meaningful workstream;
2. implement and validate locally;
3. run automated tests;
4. commit with a clear message;
5. push the branch;
6. open a pull request into `main`;
7. wait for CI;
8. review and merge;
9. delete the merged branch.

Example branch names:

```text
feature/order-forecasting
feature/shelf-recognition
feature/ml-integration
feature/system-scenarios
feature/expert-system
feature/backend-api
```

## Documentation

Detailed documentation is available in `docs/`.

Important files:

- `final_system_analysis.md` — final requirements and module responsibilities;
- `system_flow.md` — high-level and module-level flows;
- `ml_evaluation.md` — forecasting results and shelf-recognition limitations;
- `ml_contracts_final.md` — final ML and expert-system data contracts;
- `system_scenarios.md` — operational, validation, and failure scenarios;
- `architecture.md` — architectural structure;
- `requirements.md` — functional and non-functional requirements;
- `data_dictionary.md` — field definitions.

## Limitations

This repository is an educational prototype.

Current limitations include:

- synthetic historical data;
- no real shelf-image dataset;
- no trained shelf-recognition neural model;
- no production database;
- no live robot telemetry;
- incomplete expert-system, routing, assignment, and backend layers;
- no direct control of physical robots.

The project intentionally distinguishes between implemented behavior, safe fallback behavior, and planned modules.

## Disclaimer

This project was developed for educational practical training. It is not intended for production deployment or direct control of warehouse hardware.
