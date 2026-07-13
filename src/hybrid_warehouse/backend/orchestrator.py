from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hybrid_warehouse.assignment import AssignmentPipeline, build_replanning_result
from hybrid_warehouse.expert_system import MivarInferenceEngine, MivarKnowledgeBase
from hybrid_warehouse.forecasting import (
    ForecastingService,
    OrderForecastingModel,
    build_training_frame,
    load_historical_orders,
)
from hybrid_warehouse.integration import MLIntegrationService
from hybrid_warehouse.routing import RoutePlanner
from hybrid_warehouse.schemas import (
    DecisionType,
    FinalAssignmentDecision,
    ForecastResult,
    Order,
    OrderStatus,
    ReplanningResult,
    Robot,
    RobotFailureEvent,
    RobotStatus,
    RuleReloadResult,
    Shelf,
    ShelfPredictionResult,
    ShelfStatus,
    WarehousePath,
    WarehouseZone,
)
from hybrid_warehouse.schemas.entities import Product

from hybrid_warehouse.database import WarehouseRepository


class OrchestrationError(ValueError):
    """Raised when an operation cannot be executed in the current state."""


# The simulated recognizer stands in for the CNN that would be trained once
# a real shelf-image dataset exists. Known states are reported with high
# confidence; an unknown state is reported with low confidence, which the
# expert system escalates to manual review.
SIMULATED_KNOWN_CONFIDENCE = 0.92
SIMULATED_UNKNOWN_CONFIDENCE = 0.30
SIMULATED_MODEL_VERSION = "simulated-shelf-cnn-1.0"


class WarehouseOrchestrator:
    """End-to-end hybrid pipeline: ML predictions become expert-system
    facts, the mivar engine filters robots by rules, routing and ranking
    select one robot, and every decision is persisted with its explanation.
    """

    def __init__(
        self,
        project_root: str | Path,
        *,
        database_path: str | Path = ":memory:",
    ) -> None:
        self.root = Path(project_root)
        self._mock_dir = self.root / "data" / "mock"
        self._kb_dir = self.root / "data" / "knowledge_base"
        self._lock = threading.RLock()

        self.knowledge_base = MivarKnowledgeBase(
            vso_path=self._kb_dir / "mivar_vso.json",
            rules_path=self._kb_dir / "rules.json",
        )
        self.engine = MivarInferenceEngine(self.knowledge_base)
        self.integration = MLIntegrationService()
        self.repository = WarehouseRepository(database_path)

        self._train_forecasting_model()
        self.reset()

    # -- setup ---------------------------------------------------------------

    def _load_json(self, name: str) -> list[dict[str, Any]]:
        return json.loads((self._mock_dir / name).read_text(encoding="utf-8"))

    def _train_forecasting_model(self) -> None:
        history = load_historical_orders(self._mock_dir / "historical_orders.csv")
        model = OrderForecastingModel(
            n_estimators=50, random_state=42, min_samples_leaf=2
        )
        model.fit(build_training_frame(history))
        service = ForecastingService(model, model_version="random-forest-1.0")
        forecast_time = history.iloc[-1]["timestamp"].to_pydatetime() + timedelta(
            hours=1
        )
        self.forecast: ForecastResult = service.forecast_next_hour(
            history=history, forecast_time=forecast_time
        )

    def reset(self, *, clear_history: bool = True) -> None:
        """Restore the deterministic mock state; optionally keep the
        persisted decision history for a running demo."""
        with self._lock:
            self.orders: dict[str, Order] = {
                item["order_id"]: Order.model_validate(item)
                for item in self._load_json("orders.json")
            }
            self.robots: dict[str, Robot] = {
                item["robot_id"]: Robot.model_validate(item)
                for item in self._load_json("robots.json")
            }
            self.shelves: dict[str, Shelf] = {
                item["shelf_id"]: Shelf.model_validate(item)
                for item in self._load_json("shelves.json")
            }
            self.zones: list[WarehouseZone] = [
                WarehouseZone.model_validate(item)
                for item in self._load_json("zones.json")
            ]
            self.paths: list[WarehousePath] = [
                WarehousePath.model_validate(item)
                for item in self._load_json("warehouse_paths.json")
            ]
            self.products: list[Product] = [
                Product.model_validate(item)
                for item in self._load_json("products.json")
            ]

            self.route_planner = RoutePlanner(zones=self.zones, paths=self.paths)
            self.pipeline = AssignmentPipeline(self.route_planner)

            if clear_history:
                self.repository.clear_all()
            else:
                self.repository.archive_active_assignments()

    # -- ML layer --------------------------------------------------------------

    def _simulate_shelf_recognition(self, shelf: Shelf) -> ShelfPredictionResult:
        unknown = shelf.status == ShelfStatus.UNKNOWN
        confidence = (
            SIMULATED_UNKNOWN_CONFIDENCE if unknown else SIMULATED_KNOWN_CONFIDENCE
        )
        return ShelfPredictionResult(
            shelf_id=shelf.shelf_id,
            status=shelf.status,
            confidence=confidence,
            model_version=SIMULATED_MODEL_VERSION,
            prediction_time=datetime.now(timezone.utc),
            requires_manual_review=confidence < 0.60,
        )

    # -- core operations --------------------------------------------------------

    def assign_order(self, order_id: str) -> FinalAssignmentDecision:
        with self._lock:
            order = self.orders.get(order_id)
            if order is None:
                raise OrchestrationError(f"Order not found: {order_id}")
            if order.status != OrderStatus.PENDING:
                raise OrchestrationError(
                    f"Order {order_id} is not pending (current status: {order.status})."
                )

            shelf = self.shelves.get(order.shelf_id)
            if shelf is None:
                raise OrchestrationError(
                    f"Shelf {order.shelf_id} required by order {order_id} was not found."
                )

            shelf_prediction = self._simulate_shelf_recognition(shelf)
            facts = self.integration.build_facts(
                order=order,
                robots=list(self.robots.values()),
                shelf=shelf,
                shelf_prediction=shelf_prediction,
                forecast=self.forecast,
            )

            outcome = self.engine.evaluate(facts)
            decision, _ranking = self.pipeline.decide(facts, outcome)
            self.repository.save_decision(decision)

            if decision.decision == DecisionType.ASSIGNED:
                order.status = OrderStatus.ASSIGNED
                robot = self.robots[decision.selected_robot_id]
                robot.status = RobotStatus.BUSY
                robot.current_workload = robot.current_workload + 1
                robot.updated_at = datetime.now(timezone.utc)
            elif decision.decision == DecisionType.REJECTED:
                order.status = OrderStatus.REJECTED
            # MANUAL_REVIEW_REQUIRED keeps the order pending for an operator.

            return decision

    def fail_robot(
        self,
        robot_id: str,
        *,
        reason: str = "Simulated hardware failure during task execution.",
    ) -> ReplanningResult | None:
        """Mark a robot as failed; if it was executing an assignment,
        re-run the assignment pipeline for the affected order."""
        with self._lock:
            robot = self.robots.get(robot_id)
            if robot is None:
                raise OrchestrationError(f"Robot not found: {robot_id}")
            if robot.status == RobotStatus.FAILED:
                raise OrchestrationError(f"Robot {robot_id} has already failed.")

            assignment = self.repository.get_active_assignment_for_robot(robot_id)
            previous_status = str(robot.status)

            robot.status = RobotStatus.FAILED
            robot.current_workload = max(0, robot.current_workload - 1)
            robot.updated_at = datetime.now(timezone.utc)

            if assignment is None:
                return None

            self.repository.update_assignment_status(
                assignment["assignment_id"], "failed"
            )
            order = self.orders[assignment["order_id"]]
            order.status = OrderStatus.PENDING

            event = RobotFailureEvent(
                robot_id=robot_id,
                assignment_id=assignment["assignment_id"],
                order_id=assignment["order_id"],
                previous_status=previous_status,
                new_status="failed",
                failure_reason=reason,
                detected_at=datetime.now(timezone.utc),
            )

            new_decision = self.assign_order(order.order_id)
            replanning = build_replanning_result(
                event=event, new_decision=new_decision
            )
            self.repository.save_replanning(replanning)
            return replanning

    # -- knowledge-base operations ----------------------------------------------

    def reload_rules(self) -> RuleReloadResult:
        result = self.knowledge_base.reload_rules()
        self.repository.save_rule_reload(result)
        return result

    def add_rule(self, raw_rule: dict[str, Any]) -> RuleReloadResult:
        result = self.knowledge_base.add_rule(raw_rule)
        self.repository.save_rule_reload(result)
        return result

    # -- scenarios ----------------------------------------------------------------

    def load_scenarios(self) -> list[dict[str, Any]]:
        return self._load_json("scenarios.json")

    def run_scenario(self, scenario_id: str) -> dict[str, Any]:
        """Run one documented scenario from a fresh mock state and compare
        the actual outcome with the documented expectation."""
        scenarios = {item["scenario_id"]: item for item in self.load_scenarios()}
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            raise OrchestrationError(f"Scenario not found: {scenario_id}")

        with self._lock:
            self.reset(clear_history=False)

            if "failed_robot_id" in scenario:
                first_decision = self.assign_order(scenario["order_id"])
                replanning = self.fail_robot(scenario["failed_robot_id"])
                if replanning is None:
                    raise OrchestrationError(
                        "The failed robot had no active assignment to replan."
                    )
                actual = {
                    "status": str(replanning.status),
                    "replacement_robot_id": replanning.replacement_robot_id,
                }
                passed = (
                    actual["status"] == scenario["expected_status"]
                    and actual["replacement_robot_id"]
                    == scenario["expected_replacement_robot_id"]
                )
                return {
                    "scenario": scenario,
                    "passed": passed,
                    "actual": actual,
                    "first_decision": first_decision.model_dump(mode="json"),
                    "replanning": replanning.model_dump(mode="json"),
                }

            decision = self.assign_order(scenario["order_id"])
            rejected_ids = {
                rejected["robot_id"] for rejected in decision.rejected_robots
            }
            actual = {
                "decision": str(decision.decision),
                "selected_robot_id": decision.selected_robot_id,
                "rejected_robot_ids": sorted(rejected_ids),
            }
            passed = actual["decision"] == scenario["expected_decision"]
            if scenario.get("expected_selected_robot_id") is not None:
                passed = passed and (
                    actual["selected_robot_id"]
                    == scenario["expected_selected_robot_id"]
                )
            for expected_rejected in scenario.get("expected_rejected_robot_ids", []):
                passed = passed and expected_rejected in rejected_ids

            return {
                "scenario": scenario,
                "passed": passed,
                "actual": actual,
                "decision": decision.model_dump(mode="json"),
            }

    # -- read model ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "forecast": self.forecast.model_dump(mode="json"),
                "zones": [zone.model_dump(mode="json") for zone in self.zones],
                "paths": [path.model_dump(mode="json") for path in self.paths],
                "robots": [
                    robot.model_dump(mode="json") for robot in self.robots.values()
                ],
                "shelves": [
                    shelf.model_dump(mode="json") for shelf in self.shelves.values()
                ],
                "orders": [
                    order.model_dump(mode="json") for order in self.orders.values()
                ],
                "products": [
                    product.model_dump(mode="json") for product in self.products
                ],
                "active_assignments": self.repository.list_assignments(
                    status="active"
                ),
                "decisions": self.repository.list_decisions(limit=50),
                "replannings": self.repository.list_replannings(),
                "rules": [
                    rule.model_dump(mode="json")
                    for rule in self.knowledge_base.rules
                ],
                "vso_model": self.knowledge_base.vso_model,
            }
