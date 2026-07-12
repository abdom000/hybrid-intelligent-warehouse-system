# Machine Learning Evaluation

## 1. Evaluation Scope

The current prototype contains two machine-learning-related components:

1. short-term order-load forecasting;
2. shelf-status recognition.

The forecasting component has been trained and evaluated on the available historical mock dataset.

The shelf-recognition component currently provides a production-style interface, validation logic, confidence handling, and fallback behavior. It is not presented as a trained computer-vision model because no real shelf-image dataset is available in the project.

This distinction is intentional. The project should report what is implemented, what is simulated, and what remains replaceable.

---

## 2. Order Forecasting

### 2.1 Objective

The forecasting component estimates the expected number of warehouse orders for the next short-term interval.

Its output is represented by `ForecastResult` and includes:

- forecast time;
- forecast horizon;
- expected order count;
- load level;
- model version;
- generation timestamp.

The forecast does not select a robot. It provides workload context to the expert-system and assignment layers.

---

### 2.2 Dataset

The model uses the historical mock dataset stored in:

```text
data/mock/historical_orders.csv
```

The dataset contains:

- 336 historical rows;
- timestamped warehouse-order observations;
- synthetic demand behavior designed for development and integration testing.

Because the dataset is synthetic, the evaluation demonstrates pipeline correctness and comparative model performance. It does not claim production-level accuracy.

---

### 2.3 Data Preparation

The forecasting pipeline performs the following steps:

1. load historical order data;
2. validate required columns and timestamps;
3. sort records chronologically;
4. construct time-based and lag-based features;
5. split the data chronologically;
6. train the model;
7. evaluate predictions against the held-out test period.

A chronological split is used instead of randomly shuffling rows because future observations must not leak into the training period.

---

### 2.4 Train and Test Split

The evaluated dataset was divided into:

```text
Training rows: 249
Test rows: 63
```

The remaining rows are consumed by feature construction and lag requirements.

The test period occurs after the training period.

---

### 2.5 Model

The implemented forecasting model uses a tree-based regression approach through scikit-learn.

The pipeline provides:

- reproducible training;
- feature transformation;
- prediction service;
- metric generation;
- model-version metadata;
- script-based validation.

The model can later be replaced without changing the external `ForecastResult` contract.

---

### 2.6 Evaluation Metrics

The current evaluation produced:

```text
MAE: 10.0750
RMSE: 13.7329
R²: 0.9133
Baseline MAE: 16.3492
MAE improvement over baseline: 38.38%
```

#### Mean Absolute Error

MAE measures the average absolute difference between predicted and actual order counts.

```text
MAE = 10.075
```

In the mock evaluation, the prediction differs from the actual value by approximately ten orders on average.

#### Root Mean Squared Error

RMSE penalizes large prediction errors more strongly than MAE.

```text
RMSE = 13.7329
```

The difference between RMSE and MAE indicates that some observations contain larger errors.

#### Coefficient of Determination

R² measures how much variation in the target is explained by the model.

```text
R² = 0.9133
```

On the synthetic test dataset, the model explains a high proportion of target variation.

#### Baseline Comparison

The model is compared with a simpler reference prediction.

```text
Baseline MAE = 16.3492
Model MAE = 10.0750
Improvement = 38.38%
```

A baseline comparison is necessary because an isolated metric does not show whether the trained model provides useful improvement.

---

## 3. Interpretation of Forecasting Results

The forecasting pipeline successfully demonstrates:

- chronological model evaluation;
- feature-based regression;
- model comparison with a baseline;
- stable service output;
- integration with downstream schemas;
- automated validation.

The result should be described as:

> The model performs well on the synthetic development dataset and improves MAE by 38.38% over the baseline.

It should not be described as:

> The model is guaranteed to achieve the same accuracy in a real warehouse.

---

## 4. Forecast Load Levels

The predicted order count is converted into a categorical load level:

```text
low
medium
high
```

The load level gives the expert system a simpler operational signal.

Possible downstream use:

- low load: normal robot ranking;
- medium load: prefer robots with lower workload;
- high load: apply stricter workload, route-cost, or availability policies.

The exact thresholds must remain configurable and documented by the implementation.

---

## 5. Shelf Recognition

### 5.1 Intended Objective

The shelf-recognition component is intended to analyze a shelf image and return:

- shelf identifier;
- predicted shelf status;
- confidence score;
- model version;
- prediction timestamp;
- manual-review requirement.

---

### 5.2 Current Dataset Limitation

The current shelf-image manifest contains five shelf records, but no usable real shelf images are available.

The records are explicitly marked as unavailable.

Therefore, training or evaluating a real computer-vision model would produce misleading claims.

The implementation instead uses a safe fallback:

```text
status = unknown
confidence = 0.0
requires_manual_review = true
```

This preserves system integrity and allows the remaining architecture to be developed and tested.

---

### 5.3 Implemented Shelf-Recognition Functionality

The current component includes:

- predictor abstraction;
- image-path validation;
- image-format validation through Pillow;
- static predictor for deterministic tests;
- confidence handling;
- manual-review behavior;
- report generation;
- unavailable-image fallback;
- integration with `ExpertSystemFacts`.

This makes the component replaceable. A trained model can later implement the same predictor interface.

---

### 5.4 Confidence Policy

The contract uses confidence values in the inclusive range:

```text
0.0 to 1.0
```

A prediction below the accepted threshold must require manual review.

The current contract treats confidence below `0.60` as low confidence.

A low-confidence prediction must never silently become a confirmed operational fact.

---

### 5.5 Future Model Evaluation

When shelf images become available, the following evaluation should be added:

- train, validation, and test split;
- class distribution analysis;
- accuracy;
- precision;
- recall;
- F1-score;
- confusion matrix;
- per-class performance;
- confidence calibration;
- manual-review rate;
- error examples.

For an operational warehouse system, class-level recall may be more important than overall accuracy when missing an unavailable or unsafe shelf has a higher cost.

---

## 6. Integration Evaluation

The ML integration layer has been validated through:

- schema validation;
- unit tests;
- integration tests;
- an end-to-end ML demonstration.

The current end-to-end demonstration performs:

```text
Mock order
→ forecasting
→ shelf fallback
→ ML integration
→ ExpertSystemFacts
→ JSON report
```

The demo result confirmed:

```text
Order: O101
Forecasted orders: 24
Forecast load: low
Shelf status: unknown
Manual review required: true
Robots passed to expert system: 5
```

The complete automated test suite passed with:

```text
24 tests passed
```

before the boundary tests added with this document.

---

## 7. Model and Data Limitations

### Forecasting limitations

- synthetic historical data;
- limited history;
- no production seasonality;
- no external operational features;
- no concept-drift monitoring;
- no online retraining;
- no prediction-interval estimation.

### Shelf-recognition limitations

- no real training images;
- no trained neural network;
- no class-performance metrics;
- no camera or lighting evaluation;
- no confidence calibration;
- fallback-only operational behavior.

### Integration limitations

- expert-system rules are not yet complete;
- routing is not yet connected;
- assignment is not yet connected;
- no production database;
- no live robot telemetry.

---

## 8. Reproducibility

The following commands reproduce the implemented evaluation and integration behavior:

```bash
python scripts/train_forecasting_model.py
python scripts/evaluate_forecasting_model.py
python scripts/validate_shelf_recognition.py
python scripts/validate_ml_integration.py
python scripts/run_ml_end_to_end_demo.py
pytest
```

Generated reports are stored in:

```text
data/processed/
```

Model binary files are intentionally excluded from Git when configured through `.gitignore`.

---

## 9. Evaluation Conclusion

The forecasting component is implemented, evaluated, and integrated.

The shelf-recognition component is architecturally implemented but not trained because the necessary image dataset is unavailable.

The project handles this limitation safely by returning an explicit unknown state and requiring manual review.

The machine-learning layer is ready to provide validated inputs to the expert-system layer without pretending that unavailable data somehow became a neural network through optimism.
