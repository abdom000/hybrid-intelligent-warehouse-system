# Demonstration Guide

A scripted ~10-minute walkthrough that covers all three required modules:
neural prediction, the mivar expert system, and the hybrid integration.

## Preparation (before the demonstration)

```bash
# from the repository root, inside the virtual environment
python -m pip install -r requirements.txt
pytest                              # 94 tests must pass
python scripts/run_backend.py      # keep it running
```

Open `http://127.0.0.1:8000` in a browser. Press **Reset demo** to start
from the deterministic mock state.

## Step 1 — The hybrid architecture (1 min)

Point at the header tiles:

- **Forecast: 24 expected orders / load "low"** — output of the neural
  forecasting model (Module 1), trained at startup on the historical
  time series.
- **Active production rules: 11** — the mivar knowledge base (Module 2).

Message: *predictions and recognition results are never decisions — they
enter the expert system as facts, and the expert system decides.*

## Step 2 — A successful hybrid decision (2 min)

In **Orders**, click **Assign** on order **O101** (urgent, 20 kg, shelf S1).

Open the new entry in the **Decision log** and read the explanation aloud:

1. facts received (5 robots, shelf S1 recognized as `normal` with 0.92);
2. `RULE-URGENT-PRIORITIZE-SPEED` fired — an IF…THEN rule adding a constraint;
3. R2 rejected (battery below 20%), R4/R5 rejected (not available);
4. routes planned for R1 and R3 over the zone graph (Dijkstra);
5. ranking with speed-boosted weights → **R1 selected**, route
   `ZONE-A → ZONE-C → ZONE-B` (45 m).

Point at the map: R1 is now busy, order O101 is assigned.

## Step 3 — Rules protect the system (2 min)

- **O103 (54 kg):** click Assign → *rejected* — no robot has enough
  payload capacity (`RULE-ROBOT-CAPACITY` compares the robot capacity
  against the fact `order.total_weight_kg`).
- **O104 (shelf S4):** click Assign → *rejected* — `RULE-SHELF-EMPTY`.
- **O105 (shelf S5):** click Assign → *manual review required* — the
  recognition confidence is 0.30 (< 0.60), so the system refuses to act
  automatically. This is the safe-ML behaviour: an untrusted prediction
  becomes a human task, not a wrong action.

## Step 4 — Failure and replanning (1.5 min)

Press **Reset demo**, assign **O101** again (R1 takes it), then click
**⚡ Fail** on **R1**.

The replanning entry in the log shows: R1 failed → the order returned to
the queue → the same pipeline re-ran → **R3** took the order over
`ZONE-D → ZONE-C → ZONE-B`. Same rules, same routing, same ranking —
replanning is not a special case.

## Step 5 — Evolutionary knowledge-base extension (2 min)

This is the mivar highlight: **rules change at runtime, no restart**.

1. In **Knowledge base**, open *Add a new rule at runtime*. The form is
   pre-filled with: *urgent orders require at least 75% battery*.
2. Click **Add rule** — the rule count goes from 11 to 12 immediately.
3. Press **Reset demo**, then run **SCENARIO-006** (failure + replanning):
   the replanning now **fails** — R3 has only 70% battery, so the new
   rule rejects it for the urgent order. One added rule changed the
   system's behaviour live.
4. To restore the original 11 rules afterwards: remove the added block
   from `data/knowledge_base/rules.json` (it is the last entry) and click
   **Reload rules** — invalid or removed rules never require a restart.
   With git: `git checkout -- data/knowledge_base/rules.json` and reload.

## Step 6 — Scenario runner and tests (1.5 min)

Click **▶ Run** on each scenario: every card shows
**PASSED — matches expectation** (documented expected outcome vs. actual
system behaviour).

Optionally show the terminal:

```bash
python scripts/run_full_demo.py   # full pipeline in the console
pytest                            # 94 automated tests
```

And the auto-generated API documentation at `http://127.0.0.1:8000/docs`.

## Likely questions

- **Why "mivar"?** The domain is modelled as Things–Properties–Relations
  (VSO); rules are declarative data over registered properties, inference
  builds a chain from known facts to the goal (a robot assignment) and
  the chain itself is the explanation. The knowledge base evolves at
  runtime, which is a defining mivar property.
- **Where exactly do the neural networks feed the expert system?**
  `MLIntegrationService.build_facts(...)` converts `ForecastResult` and
  `ShelfPredictionResult` into `ExpertSystemFacts` — the only input the
  engine accepts.
- **Why is shelf recognition simulated?** No labelled shelf-image dataset
  exists. The simulator honours the exact predictor contract, so a
  trained CNN is a drop-in replacement (`ShelfStatusPredictor` protocol).
- **Is the decision reproducible?** Yes — mock data is deterministic,
  ranking is deterministic with an explicit tie-break, and every decision
  is persisted with its explanation in SQLite.
