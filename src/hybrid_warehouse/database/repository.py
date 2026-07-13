from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

from hybrid_warehouse.schemas import (
    FinalAssignmentDecision,
    ReplanningResult,
    RuleReloadResult,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    selected_robot_id TEXT,
    assignment_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assignments (
    assignment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    robot_id TEXT NOT NULL,
    status TEXT NOT NULL,
    route_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS replannings (
    previous_assignment_id TEXT NOT NULL,
    new_assignment_id TEXT,
    order_id TEXT NOT NULL,
    failed_robot_id TEXT NOT NULL,
    replacement_robot_id TEXT,
    status TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    replanned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_reloads (
    success INTEGER NOT NULL,
    loaded_rules INTEGER NOT NULL,
    rejected_rules INTEGER NOT NULL,
    errors_json TEXT NOT NULL,
    reloaded_at TEXT NOT NULL
);
"""


class WarehouseRepository:
    """SQLite persistence for decisions, assignments, and replanning history.

    Every stored row keeps the full JSON payload, so the dashboard and any
    later analysis can reconstruct the complete explanation of a decision.
    """

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        if self._database_path != ":memory:":
            Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self._database_path, check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row
        with self._lock, self._connection:
            self._connection.executescript(_SCHEMA)

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    # -- write operations ---------------------------------------------------

    def save_decision(self, decision: FinalAssignmentDecision) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    decision.decision_id,
                    decision.order_id,
                    str(decision.decision),
                    decision.selected_robot_id,
                    decision.assignment_id,
                    json.dumps(decision.model_dump(mode="json")),
                    decision.created_at.isoformat(),
                ),
            )
            if decision.assignment_id and decision.selected_robot_id:
                self._connection.execute(
                    "INSERT INTO assignments VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        decision.assignment_id,
                        decision.order_id,
                        decision.selected_robot_id,
                        "active",
                        json.dumps(decision.route),
                        decision.created_at.isoformat(),
                        decision.created_at.isoformat(),
                    ),
                )

    def update_assignment_status(self, assignment_id: str, status: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE assignments SET status = ?, updated_at = datetime('now') "
                "WHERE assignment_id = ?",
                (status, assignment_id),
            )

    def save_replanning(self, result: ReplanningResult) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO replannings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    result.previous_assignment_id,
                    result.new_assignment_id,
                    result.order_id,
                    result.failed_robot_id,
                    result.replacement_robot_id,
                    str(result.status),
                    json.dumps(result.model_dump(mode="json")),
                    result.replanned_at.isoformat(),
                ),
            )

    def save_rule_reload(self, result: RuleReloadResult) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO rule_reloads VALUES (?, ?, ?, ?, ?)",
                (
                    int(result.success),
                    result.loaded_rules,
                    result.rejected_rules,
                    json.dumps(result.errors),
                    result.reloaded_at.isoformat(),
                ),
            )

    def archive_active_assignments(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE assignments SET status = 'archived', "
                "updated_at = datetime('now') WHERE status = 'active'"
            )

    def clear_all(self) -> None:
        with self._lock, self._connection:
            for table in ("decisions", "assignments", "replannings", "rule_reloads"):
                self._connection.execute(f"DELETE FROM {table}")

    # -- read operations ------------------------------------------------------

    def list_decisions(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload_json FROM decisions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT payload_json FROM decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def list_assignments(self, *, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM assignments"
        parameters: tuple[Any, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY created_at DESC"
        with self._lock:
            rows = self._connection.execute(query, parameters).fetchall()
        return [
            {**dict(row), "route": json.loads(row["route_json"])}
            for row in rows
        ]

    def get_active_assignment_for_robot(self, robot_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM assignments WHERE robot_id = ? AND status = 'active' "
                "ORDER BY created_at DESC LIMIT 1",
                (robot_id,),
            ).fetchone()
        if row is None:
            return None
        return {**dict(row), "route": json.loads(row["route_json"])}

    def list_replannings(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload_json FROM replannings ORDER BY replanned_at DESC"
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]
