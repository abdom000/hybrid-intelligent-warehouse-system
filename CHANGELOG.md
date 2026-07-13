# Changelog

## 1.0.0 — Full hybrid system

- Added the mivar knowledge base: VSO domain model (`data/knowledge_base/mivar_vso.json`) and hot-reloadable production rules (`data/knowledge_base/rules.json`).
- Implemented the expert-system module: forward-chaining inference engine, rule validation against the VSO model, runtime rule addition and reload without restart.
- Implemented the routing module: Dijkstra shortest-path planning over active zones and paths.
- Implemented the assignment module: constraint-aware robot ranking, final explainable decisions, and failure-triggered replanning.
- Implemented SQLite persistence for decisions, assignments, replannings, and rule reloads.
- Implemented the backend: full pipeline orchestrator, FastAPI application, and an interactive demo dashboard.
- Added a scenario runner covering all six documented system scenarios (expected vs. actual).
- Added `scripts/run_backend.py` and `scripts/run_full_demo.py`.
- Extended the test suite to 94 tests, including end-to-end scenario and HTTP API coverage.
- Added `docs/demo_guide.md` and updated the README for the completed system.

## 0.1.0 — Data Science foundation

- Project structure, documentation, and deterministic mock warehouse data.
- Shared Pydantic schemas and validation scripts.
- Order-forecasting pipeline with chronological evaluation and baseline comparison.
- Shelf-recognition interface with confidence policy and safe no-image fallback.
- ML integration producing validated `ExpertSystemFacts`.
- GitHub Actions CI with automated unit and integration tests.
