import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hybrid_warehouse.expert_system import (
    MANUAL_REVIEW_REQUIRED,
    ORDER_REJECTED,
    MivarInferenceEngine,
    MivarKnowledgeBase,
)
from hybrid_warehouse.schemas import ExpertSystemFacts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def build_facts(
    *,
    priority: str = "normal",
    total_weight_kg: float = 20.0,
    shelf_status: str = "normal",
    shelf_confidence: float = 0.95,
    requires_manual_review: bool = False,
    load_level: str = "low",
    robots: list[dict] | None = None,
) -> ExpertSystemFacts:
    if robots is None:
        robots = [
            {
                "robot_id": "R1",
                "battery_level": 90.0,
                "maximum_load_kg": 50.0,
                "current_zone_id": "ZONE-A",
                "current_workload": 0,
                "status": "available",
            }
        ]
    return ExpertSystemFacts.model_validate(
        {
            "order": {
                "order_id": "O1",
                "priority": priority,
                "total_weight_kg": total_weight_kg,
                "shelf_id": "S1",
            },
            "robots": robots,
            "shelf": {
                "shelf_id": "S1",
                "zone_id": "ZONE-B",
                "status": shelf_status,
                "confidence": shelf_confidence,
                "requires_manual_review": requires_manual_review,
            },
            "forecast": {"expected_orders": 24, "load_level": load_level},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@pytest.fixture(scope="module")
def engine() -> MivarInferenceEngine:
    knowledge_base = MivarKnowledgeBase(
        vso_path=KB_DIR / "mivar_vso.json",
        rules_path=KB_DIR / "rules.json",
    )
    return MivarInferenceEngine(knowledge_base)


def test_available_robot_with_capacity_is_eligible(engine):
    outcome = engine.evaluate(build_facts())
    assert outcome.result.eligible_robot_ids == ["R1"]
    assert outcome.result.rejected_robots == []
    assert ORDER_REJECTED not in outcome.result.decision_constraints


def test_low_battery_robot_is_rejected(engine):
    facts = build_facts(
        robots=[
            {
                "robot_id": "R2",
                "battery_level": 15.0,
                "maximum_load_kg": 50.0,
                "current_zone_id": "ZONE-A",
                "current_workload": 0,
                "status": "available",
            }
        ]
    )
    outcome = engine.evaluate(facts)
    assert outcome.result.eligible_robot_ids == []
    rejected = outcome.result.rejected_robots[0]
    assert rejected.robot_id == "R2"
    assert "RULE-ROBOT-LOW-BATTERY" in rejected.applied_rules


def test_unavailable_robot_is_rejected(engine):
    facts = build_facts(
        robots=[
            {
                "robot_id": "R4",
                "battery_level": 90.0,
                "maximum_load_kg": 50.0,
                "current_zone_id": "ZONE-A",
                "current_workload": 1,
                "status": "busy",
            }
        ]
    )
    outcome = engine.evaluate(facts)
    assert outcome.result.eligible_robot_ids == []
    assert "RULE-ROBOT-NOT-AVAILABLE" in outcome.result.rejected_robots[0].applied_rules


def test_capacity_rule_compares_against_order_weight_fact(engine):
    facts = build_facts(
        total_weight_kg=54.0,
        robots=[
            {
                "robot_id": "R1",
                "battery_level": 90.0,
                "maximum_load_kg": 50.0,
                "current_zone_id": "ZONE-A",
                "current_workload": 0,
                "status": "available",
            }
        ],
    )
    outcome = engine.evaluate(facts)
    assert outcome.result.eligible_robot_ids == []
    assert "RULE-ROBOT-CAPACITY" in outcome.result.rejected_robots[0].applied_rules


def test_empty_shelf_rejects_the_order(engine):
    outcome = engine.evaluate(build_facts(shelf_status="empty"))
    assert ORDER_REJECTED in outcome.result.decision_constraints
    assert "RULE-SHELF-EMPTY" in outcome.result.applied_rules


def test_unknown_shelf_requires_manual_review(engine):
    outcome = engine.evaluate(
        build_facts(
            shelf_status="unknown",
            shelf_confidence=0.30,
            requires_manual_review=True,
        )
    )
    assert MANUAL_REVIEW_REQUIRED in outcome.result.decision_constraints


def test_urgent_order_adds_speed_constraint(engine):
    outcome = engine.evaluate(build_facts(priority="urgent"))
    assert "prioritize_speed" in outcome.result.decision_constraints


def test_high_load_forecast_rejects_low_battery_reserve(engine):
    facts = build_facts(
        load_level="high",
        robots=[
            {
                "robot_id": "R3",
                "battery_level": 35.0,
                "maximum_load_kg": 50.0,
                "current_zone_id": "ZONE-A",
                "current_workload": 0,
                "status": "available",
            }
        ],
    )
    outcome = engine.evaluate(facts)
    assert outcome.result.eligible_robot_ids == []
    assert (
        "RULE-HIGH-LOAD-BATTERY-RESERVE"
        in outcome.result.rejected_robots[0].applied_rules
    )


def test_every_decision_is_traceable(engine):
    outcome = engine.evaluate(build_facts(priority="urgent"))
    assert outcome.trace
    assert any("RULE-URGENT-PRIORITIZE-SPEED" in step for step in outcome.trace)


# -- hot reload and evolutionary extension ------------------------------------


@pytest.fixture()
def kb_copy(tmp_path) -> MivarKnowledgeBase:
    shutil.copy(KB_DIR / "mivar_vso.json", tmp_path / "mivar_vso.json")
    shutil.copy(KB_DIR / "rules.json", tmp_path / "rules.json")
    return MivarKnowledgeBase(
        vso_path=tmp_path / "mivar_vso.json",
        rules_path=tmp_path / "rules.json",
    )


def new_rule(rule_id: str = "RULE-TEST-NEW") -> dict:
    return {
        "rule_id": rule_id,
        "name": "Test rule",
        "description": "IF the order is urgent THEN prefer fast robots.",
        "conditions": [
            {"field": "order.priority", "operator": "==", "value": "urgent"}
        ],
        "actions": [{"type": "add_constraint", "reason": "test_constraint"}],
        "priority": 10,
        "active": True,
        "version": "1.0.0",
    }


def test_initial_load_accepts_all_shipped_rules(kb_copy):
    assert len(kb_copy.rules) >= 10
    assert all(rule.active for rule in kb_copy.active_rules)


def test_add_rule_is_applied_without_restart(kb_copy):
    count_before = len(kb_copy.rules)
    result = kb_copy.add_rule(new_rule())
    assert result.success
    assert len(kb_copy.rules) == count_before + 1

    engine = MivarInferenceEngine(kb_copy)
    facts_payload = build_facts(priority="urgent")
    outcome = engine.evaluate(facts_payload)
    assert "test_constraint" in outcome.result.decision_constraints


def test_added_rule_is_persisted_to_disk(kb_copy, tmp_path):
    kb_copy.add_rule(new_rule())
    stored = json.loads((tmp_path / "rules.json").read_text(encoding="utf-8"))
    assert any(rule["rule_id"] == "RULE-TEST-NEW" for rule in stored)


def test_duplicate_rule_id_is_rejected(kb_copy):
    assert kb_copy.add_rule(new_rule()).success
    result = kb_copy.add_rule(new_rule())
    assert not result.success
    assert result.rejected_rules == 1


def test_rule_with_unknown_vso_property_is_rejected(kb_copy):
    rule = new_rule("RULE-BAD-FIELD")
    rule["conditions"] = [{"field": "robot.color", "operator": "==", "value": "red"}]
    result = kb_copy.add_rule(rule)
    assert not result.success
    assert "not a registered VSO property" in result.errors[0]["error"]


def test_reload_keeps_valid_rules_and_reports_invalid_ones(kb_copy, tmp_path):
    rules_path = tmp_path / "rules.json"
    stored = json.loads(rules_path.read_text(encoding="utf-8"))
    stored.append({"rule_id": "RULE-BROKEN"})  # missing required fields
    rules_path.write_text(json.dumps(stored), encoding="utf-8")

    result = kb_copy.reload_rules()
    assert not result.success
    assert result.rejected_rules == 1
    assert result.loaded_rules == len(stored) - 1
    assert result.errors[0]["rule_id"] == "RULE-BROKEN"
