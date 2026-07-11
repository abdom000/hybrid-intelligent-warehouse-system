# Project Scope

## Document Information

| Field | Value |
|---|---|
| Project name | Hybrid Intelligent Warehouse System |
| Document version | 0.1 |
| Project type | Educational summer practical-training project |
| Team size | 2 participants |
| Current phase | Requirements analysis and project initialization |

## 1. Project Background

Large warehouse complexes process a high number of orders every day. Warehouse operations require continuous decisions regarding:

- which robot should execute an order;
- whether a robot has sufficient battery and load capacity;
- whether the required product is available on a shelf;
- how urgent orders should be prioritized;
- how the system should react to robot failures;
- how predicted warehouse workload should affect robot allocation.

Manual task assignment becomes inefficient when the number of orders, robots, shelves, and operational constraints increases.

The project will develop an educational prototype of a hybrid intelligent system that combines machine-learning predictions with rule-based logical reasoning.

## 2. Problem Statement

The main problem is the automatic assignment of warehouse delivery robots to orders while considering multiple operational factors.

The system must use:

1. historical order data to forecast warehouse workload;
2. shelf images to recognize shelf conditions;
3. current warehouse facts to evaluate available robots;
4. logical rules to select or reject robots;
5. explanations to justify each decision;
6. replanning logic when failures or operational changes occur.

## 3. Project Goal

The goal of the project is to design and implement a prototype hybrid intelligent warehouse system that:

- forecasts future warehouse order volume;
- recognizes shelf conditions from images;
- converts machine-learning outputs into structured facts;
- applies logical rules to warehouse facts;
- assigns suitable robots to orders;
- explains the reasoning behind decisions;
- supports rule updates without restarting the complete system.

## 4. Project Objectives

The project objectives are:

1. define the system requirements and operational scenarios;
2. design warehouse entities, properties, and relations;
3. prepare mock and synthetic datasets;
4. develop an order-flow forecasting model;
5. develop a shelf-image classification model;
6. design a VSO-based knowledge representation;
7. implement logical `IF...THEN` rules;
8. implement robot filtering and ranking;
9. expose system functions through an API;
10. integrate the Data Science and expert-system modules;
11. test the complete decision flow;
12. document the architecture, data, results, and limitations.

## 5. MVP Scope

The Minimum Viable Product will support one complete warehouse decision scenario.

The MVP will:

1. receive one pending warehouse order;
2. receive a list of available warehouse robots;
3. receive information about products, shelves, and warehouse zones;
4. forecast warehouse workload for the next hour;
5. classify one shelf image;
6. convert prediction outputs into expert-system facts;
7. reject robots that do not satisfy mandatory constraints;
8. rank the remaining robots;
9. assign the most suitable robot to the order;
10. return an explanation of the decision;
11. reassign the order if the selected robot fails;
12. load updated logical rules without rebuilding the application.

## 6. In-Scope Features

### 6.1 System Analysis

The project includes:

- definition of functional requirements;
- definition of non-functional requirements;
- definition of system actors and use cases;
- definition of warehouse entities;
- definition of data fields and data types;
- definition of module interfaces;
- definition of acceptance criteria;
- documentation of assumptions and limitations.

### 6.2 Order Forecasting

The forecasting module includes:

- historical or synthetic time-series data;
- time-based feature engineering;
- seasonality and holiday-related features;
- a simple baseline model;
- at least one machine-learning model;
- model evaluation;
- model serialization;
- a prediction function;
- structured prediction output.

The initial forecast horizon is:

```text
Next one hour
```

### 6.3 Shelf Recognition

The shelf-recognition module includes:

- an image dataset or an approved educational substitute;
- image preprocessing;
- training, validation, and test partitions;
- transfer learning using a pretrained neural-network model;
- model evaluation;
- model serialization;
- a prediction function;
- predicted class and confidence score.

The initial shelf classes are:

```text
empty
low_stock
normal
full
```

### 6.4 Expert System

The expert-system module includes:

- VSO-based warehouse knowledge representation;
- warehouse facts;
- logical `IF...THEN` rules;
- mandatory robot eligibility checks;
- robot-ranking logic;
- decision explanations;
- failure-handling rules;
- rule loading from an external source.

### 6.5 Robot Assignment

Robot assignment will consider:

- robot availability;
- robot status;
- robot battery level;
- robot load capacity;
- order weight;
- order priority;
- robot location;
- shelf location;
- route distance;
- current robot workload;
- predicted warehouse workload.

### 6.6 Backend and API

The backend includes:

- API endpoints;
- request and response validation;
- database access;
- integration with trained models;
- integration with the expert system;
- error handling;
- basic logging;
- API documentation.

### 6.7 Data Storage

The planned database will store:

- warehouse zones;
- robots;
- products;
- shelves;
- orders;
- assignments;
- forecasts;
- shelf predictions;
- expert-system rules;
- decision records.

The planned database technology is PostgreSQL.

## 7. Out-of-Scope Features

The following features are not included in the MVP:

- direct control of physical robots;
- communication with real robot hardware;
- real-time camera streaming;
- real production warehouse integration;
- advanced user authentication;
- role-based user management;
- mobile applications;
- complex web frontend;
- distributed microservices;
- Kubernetes deployment;
- Kafka-based event streaming;
- large-scale production monitoring;
- automatic product detection using bounding boxes;
- commercial route optimization for thousands of robots;
- guaranteed mathematical global optimization;
- production-level cybersecurity certification.

These features may be considered future extensions but are not required for successful completion of the internship prototype.

## 8. System Actors

### 8.1 Warehouse Operator

The warehouse operator can:

- submit or inspect an order;
- view robot-assignment decisions;
- view explanations;
- inspect robot and shelf conditions;
- trigger reassignment after a failure.

### 8.2 Data Scientist

The Data Scientist can:

- prepare data;
- train models;
- evaluate models;
- generate predictions;
- update model artifacts.

### 8.3 Knowledge Engineer or Administrator

The knowledge engineer can:

- inspect logical rules;
- add or update rules;
- activate or deactivate rules;
- reload the knowledge base.

### 8.4 External Camera or Image Source

The image source provides shelf images to the shelf-recognition module.

For the MVP, this actor may be simulated using uploaded image files.

## 9. Team Responsibilities

### 9.1 Abdelrahman : System Analyst / Data Scientist

Responsible for:

- requirements analysis;
- project-scope definition;
- use-case definition;
- data requirements;
- data dictionary;
- mock-data generation;
- exploratory data analysis;
- order-flow forecasting;
- shelf-image classification;
- model evaluation;
- model artifact preparation;
- machine-learning output contracts;
- Data Science tests;
- Data Science documentation.

### 9.2 Halit : Backend / Expert System Developer

Responsible for:

- backend architecture;
- database models;
- database access;
- VSO knowledge-base design;
- expert-system facts;
- logical rules;
- inference engine;
- robot filtering;
- robot ranking;
- route calculation;
- API endpoints;
- rule reloading;
- backend tests;
- integration implementation.

### 9.3 Shared Responsibilities

Both participants are responsible for:

- architecture review;
- interface-contract agreement;
- Git and GitHub workflow;
- pull-request review;
- end-to-end integration;
- acceptance testing;
- README maintenance;
- final demonstration;
- internship documentation.

## 10. Main System Flow

The planned system flow is:

```text
Historical order data
        ↓
Forecasting model
        ↓
Expected warehouse workload
        ↓
        ┐
        │
Shelf image
        ↓
Shelf-recognition model
        ↓
Shelf status and confidence
        │
        ┘
        ↓
Structured warehouse facts
        ↓
Expert system
        ↓
Robot eligibility filtering
        ↓
Robot ranking and route evaluation
        ↓
Robot assignment or order rejection
        ↓
Decision explanation
```

## 11. Main Business Scenario

The main business scenario is:

1. a new warehouse order is received;
2. the required product and shelf are identified;
3. the shelf condition is obtained from the image model;
4. the expected warehouse workload is obtained from the forecasting model;
5. current robot information is loaded;
6. unavailable or unsuitable robots are rejected;
7. suitable robots receive ranking scores;
8. the highest-ranked robot is selected;
9. a route is calculated;
10. the system returns the assignment and explanation;
11. if the robot fails, the order is reassigned.

## 12. Initial Business Rules

The initial rule set will include rules such as:

1. a robot must be available;
2. a failed robot cannot receive an order;
3. robot capacity must be greater than or equal to order weight;
4. robot battery must be above the minimum threshold;
5. an empty shelf blocks the picking operation;
6. low recognition confidence requires manual inspection;
7. urgent orders receive higher priority;
8. robots nearer to the shelf receive a better ranking;
9. heavily loaded robots receive a ranking penalty;
10. failed assignments must be replanned;
11. high predicted warehouse workload may activate reserve robots.

The final rules will be documented separately in the expert-system documentation.

## 13. Data Sources

The project may use:

- synthetic order-history data;
- manually prepared mock robot data;
- manually prepared mock order data;
- manually prepared warehouse-zone data;
- a public or educational shelf-image dataset;
- manually collected shelf images where legally and practically appropriate.

All synthetic and mock data must be clearly identified as non-production data.

## 14. Assumptions

The project assumes that:

- each order refers to one primary product for the MVP;
- each product is associated with one primary shelf;
- warehouse zones can be represented as a graph;
- robot state information is available;
- shelf images are provided as files;
- model predictions do not directly control hardware;
- the expert system receives prediction results in a defined JSON structure;
- physical execution of robot tasks is simulated.

## 15. Constraints

The project is constrained by:

- a two-person team;
- limited practical-training duration;
- absence of real warehouse infrastructure;
- absence of real robot hardware;
- limited or unavailable production datasets;
- limited computing resources;
- educational rather than production requirements.

## 16. Deliverables

The planned deliverables are:

- GitHub repository;
- requirements documentation;
- project-scope documentation;
- architecture documentation;
- data dictionary;
- data contracts;
- mock and synthetic datasets;
- trained forecasting model;
- trained shelf-recognition model or justified prototype;
- expert-system knowledge base;
- logical rules;
- backend API;
- database schema;
- automated tests;
- end-to-end demonstration;
- README;
- internship report;
- internship diary;
- final presentation materials.

## 17. Acceptance Criteria

The MVP will be considered successful when:

1. the repository can be installed and run using documented instructions;
2. the forecasting module returns a valid next-hour forecast;
3. the shelf-recognition module returns a supported class and confidence score;
4. ML outputs follow the agreed data contract;
5. the expert system rejects robots that violate mandatory constraints;
6. the system selects a suitable robot when one is available;
7. the system returns a human-readable explanation;
8. the system returns a valid rejection reason when no robot is suitable;
9. robot failure triggers reassignment logic;
10. a logical rule can be added or updated without changing the main application code;
11. unit and integration tests cover the main scenario;
12. the complete scenario can be demonstrated from input to final decision.

## 18. Risks

| Risk | Impact | Planned Response |
|---|---|---|
| No real warehouse data | Forecasting may not represent production behavior | Use clearly documented synthetic data |
| Insufficient shelf images | Image model may overfit | Use transfer learning and limit the number of classes |
| Integration delay | Modules may work separately but fail together | Define data contracts before implementation |
| Scope growth | Project may not be completed | Keep optional features outside the MVP |
| Different output formats | Backend may not understand ML outputs | Validate JSON contracts early |
| Model accuracy limitations | Predictions may be unreliable | Compare with baselines and document limitations |
| Git conflicts | Team work may be lost or delayed | Use task branches and pull-request reviews |

## 19. Change Control

Changes to the project scope must:

1. be discussed by both participants;
2. include a reason;
3. identify the affected modules;
4. identify schedule impact;
5. update this document if approved.

Major technical decisions should be recorded in:

```text
docs/decisions/
```

## 20. Future Extensions

Possible future extensions include:

- real robot integration;
- real-time camera streams;
- object detection;
- multi-product orders;
- multi-robot task optimization;
- advanced route optimization;
- real-time event processing;
- user authentication;
- monitoring dashboards;
- production deployment;
- automatic model retraining;
- larger mivar knowledge bases.

## 21. Scope Approval

This document represents the initial agreed project scope.

The scope may be refined during the requirements-analysis phase, but changes must remain compatible with the project timeline and the two-person team capacity.