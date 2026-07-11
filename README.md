# Hybrid Intelligent Warehouse System

A hybrid intelligent system for optimizing warehouse operations by combining machine learning, computer vision, and rule-based logical reasoning.

## Project Overview

Large warehouses process many orders every day. Assigning delivery robots manually becomes difficult when the system must consider several factors, such as:

- order priority;
- product location;
- robot availability;
- robot battery level;
- robot load capacity;
- shelf condition;
- predicted warehouse workload.

This project develops an educational prototype that uses machine-learning models to generate predictions and an expert system to make explainable operational decisions.

## Main Objectives

The system will:

1. forecast the expected number of warehouse orders;
2. classify shelf conditions from images;
3. convert machine-learning outputs into facts;
4. apply logical rules to select a suitable robot;
5. explain why a robot was selected or rejected;
6. reassign tasks when failures or operational changes occur;
7. support adding or updating logical rules without stopping the system.

## System Modules

### 1. Order Forecasting

Predicts future warehouse order volume using historical time-series data, seasonality, calendar-related features, and holiday information.

### 2. Shelf Recognition

Classifies warehouse shelf images into one of the following categories:

- `empty`;
- `low_stock`;
- `normal`;
- `full`.

### 3. Expert System

Uses warehouse facts and `IF...THEN` rules to:

- filter unsuitable robots;
- rank suitable robots;
- assign robots to orders;
- explain decisions;
- replan tasks after failures;
- react to changes in shelf conditions and warehouse workload.

### 4. Backend and Integration

Connects the machine-learning modules, expert system, database, routing logic, and API.

## Team

### Abdelrahman : System Analyst / Data Scientist

Responsibilities:

- requirements analysis;
- project scope definition;
- system and data analysis;
- mock-data generation;
- order-flow forecasting;
- shelf-image classification;
- model evaluation;
- machine-learning output contracts;
- Data Science documentation.

### Halit : Backend / Expert System Developer

Responsibilities:

- backend development;
- database integration;
- VSO knowledge-base design;
- logical rule development;
- inference engine implementation;
- robot assignment logic;
- route planning;
- API development;
- system integration.

## Planned Technologies

- Python
- pandas
- NumPy
- scikit-learn
- PyTorch
- torchvision
- FastAPI
- Pydantic
- PostgreSQL
- SQLAlchemy
- NetworkX
- pytest
- Docker
- Git
- GitHub

The technology list may change after the architecture and technical requirements are finalized.

## Repository Structure

```text
.
├── data/
│   ├── mock/                   Generated mock data
│   ├── processed/              Cleaned and transformed data
│   └── raw/                    Original input data
├── docs/
│   ├── decisions/              Architecture decision records
│   ├── architecture.md         System architecture
│   ├── data_contracts.md       Data exchange formats
│   ├── data_dictionary.md      Data field definitions
│   ├── project_scope.md        Project boundaries and MVP scope
│   ├── requirements.md         Functional and non-functional requirements
│   └── roadmap.md              Project implementation plan
├── notebooks/
│   ├── forecasting/            Forecasting experiments
│   └── shelf_recognition/      Computer-vision experiments
├── scripts/                    Utility and execution scripts
├── src/
│   └── hybrid_warehouse/
│       ├── backend/             API and database logic
│       ├── expert_system/       Knowledge base and inference engine
│       ├── forecasting/         Order-flow forecasting module
│       ├── integration/         End-to-end orchestration
│       └── shelf_recognition/   Shelf image-classification module
├── tests/
│   ├── integration/             Integration tests
│   └── unit/                    Unit tests
├── .env.example                 Environment variable template
├── .gitignore                   Files excluded from Git
├── CHANGELOG.md                 Important project changes
├── CONTRIBUTING.md              Team workflow and contribution rules
├── pyproject.toml               Python project and tool configuration
├── README.md                    Main project documentation
└── requirements.txt             Python dependencies
```

## MVP

The first working version of the system will:

1. receive one warehouse order;
2. receive information about available robots;
3. receive information about shelves, products, and warehouse zones;
4. forecast warehouse workload for the next hour;
5. classify the condition of a shelf from an image;
6. reject unsuitable robots;
7. select the most suitable robot;
8. return an explanation of the decision;
9. support task reassignment after a robot failure;
10. support adding or updating logical rules without restarting the system.

## Example System Flow

```text
Historical order data
        ↓
Order forecasting model
        ↓
Predicted warehouse workload
        ↓
        ┐
        │
Shelf image
        ↓
Shelf recognition model
        ↓
Detected shelf condition
        │
        ┘
        ↓
Expert system
        ↓
Robot filtering and ranking
        ↓
Robot assignment
        ↓
Decision and explanation
```

## Project Status

Current phase:

```text
Project initialization and requirements analysis
```

## Documentation

Detailed project documentation is located in the `docs/` directory:

- `project_scope.md`;
- `requirements.md`;
- `roadmap.md`;
- `architecture.md`;
- `data_contracts.md`;
- `data_dictionary.md`.

## Development Workflow

The team will use a branch-based Git workflow:

1. create a branch for each task;
2. implement and test the task;
3. commit changes using a clear message;
4. push the branch to GitHub;
5. create a pull request;
6. review the changes;
7. merge approved work into the `main` branch.

Example branch names:

```text
feature/project-setup
feature/order-forecasting
feature/shelf-classification
feature/expert-system
feature/backend-api
feature/system-integration
```

## Disclaimer

This project is an educational prototype developed as part of summer practical training.

It does not directly control physical warehouse robots and is not intended for production deployment.