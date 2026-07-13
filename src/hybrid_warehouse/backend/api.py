from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from hybrid_warehouse.expert_system import KnowledgeBaseError

from .orchestrator import OrchestrationError, WarehouseOrchestrator

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _default_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _error_payload(code: str, message: str) -> dict[str, Any]:
    return {
        "error_code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def create_app(
    project_root: str | Path | None = None,
    *,
    database_path: str | Path | None = None,
) -> FastAPI:
    root = Path(project_root) if project_root is not None else _default_project_root()
    if database_path is None:
        database_path = os.environ.get(
            "WAREHOUSE_DB_PATH", str(root / "data" / "warehouse.db")
        )

    app = FastAPI(
        title="HiveWare — Hybrid Intelligent Warehouse System",
        description=(
            "Hybrid pipeline: neural forecasting and shelf recognition feed "
            "facts into a mivar expert system that assigns warehouse robots."
        ),
        version="1.0.0",
    )
    orchestrator = WarehouseOrchestrator(root, database_path=database_path)
    app.state.orchestrator = orchestrator

    @app.exception_handler(OrchestrationError)
    async def orchestration_error_handler(_, error: OrchestrationError):
        return JSONResponse(
            status_code=409,
            content=_error_payload("orchestration_error", str(error)),
        )

    @app.exception_handler(KnowledgeBaseError)
    async def knowledge_base_error_handler(_, error: KnowledgeBaseError):
        return JSONResponse(
            status_code=400,
            content=_error_payload("knowledge_base_error", str(error)),
        )

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/state")
    def get_state() -> dict[str, Any]:
        return orchestrator.get_state()

    @app.get("/api/forecast")
    def get_forecast() -> dict[str, Any]:
        return orchestrator.forecast.model_dump(mode="json")

    @app.post("/api/orders/{order_id}/assign")
    def assign_order(order_id: str) -> dict[str, Any]:
        decision = orchestrator.assign_order(order_id)
        return decision.model_dump(mode="json")

    @app.post("/api/robots/{robot_id}/fail")
    def fail_robot(robot_id: str) -> dict[str, Any]:
        replanning = orchestrator.fail_robot(robot_id)
        if replanning is None:
            return {
                "replanned": False,
                "message": (
                    f"Robot {robot_id} was marked as failed. It had no active "
                    "assignment, so no replanning was required."
                ),
            }
        return {"replanned": True, **replanning.model_dump(mode="json")}

    @app.get("/api/decisions")
    def list_decisions() -> list[dict[str, Any]]:
        return orchestrator.repository.list_decisions()

    @app.get("/api/replannings")
    def list_replannings() -> list[dict[str, Any]]:
        return orchestrator.repository.list_replannings()

    @app.get("/api/rules")
    def list_rules() -> list[dict[str, Any]]:
        return [
            rule.model_dump(mode="json") for rule in orchestrator.knowledge_base.rules
        ]

    @app.post("/api/rules")
    def add_rule(raw_rule: dict[str, Any]) -> dict[str, Any]:
        result = orchestrator.add_rule(raw_rule)
        payload = result.model_dump(mode="json")
        if not result.success:
            raise HTTPException(status_code=422, detail=payload)
        return payload

    @app.post("/api/rules/reload")
    def reload_rules() -> dict[str, Any]:
        return orchestrator.reload_rules().model_dump(mode="json")

    @app.get("/api/scenarios")
    def list_scenarios() -> list[dict[str, Any]]:
        return orchestrator.load_scenarios()

    @app.post("/api/scenarios/{scenario_id}/run")
    def run_scenario(scenario_id: str) -> dict[str, Any]:
        return orchestrator.run_scenario(scenario_id)

    @app.post("/api/reset")
    def reset() -> dict[str, Any]:
        orchestrator.reset(clear_history=True)
        return {"status": "reset", "message": "Mock state and history restored."}

    return app
