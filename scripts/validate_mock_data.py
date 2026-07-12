from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MOCK_DIR = ROOT / "data" / "mock"


def load_json(filename: str) -> Any:
    with (MOCK_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    products = load_json("products.json")
    shelves = load_json("shelves.json")
    zones = load_json("zones.json")
    paths = load_json("warehouse_paths.json")
    robots = load_json("robots.json")
    orders = load_json("orders.json")
    scenarios = load_json("scenarios.json")

    product_ids = {item["product_id"] for item in products}
    shelf_ids = {item["shelf_id"] for item in shelves}
    zone_ids = {item["zone_id"] for item in zones}
    robot_ids = {item["robot_id"] for item in robots}
    order_ids = {item["order_id"] for item in orders}

    require(len(product_ids) == len(products), "Duplicate product_id found.")
    require(len(shelf_ids) == len(shelves), "Duplicate shelf_id found.")
    require(len(zone_ids) == len(zones), "Duplicate zone_id found.")
    require(len(robot_ids) == len(robots), "Duplicate robot_id found.")
    require(len(order_ids) == len(orders), "Duplicate order_id found.")

    for shelf in shelves:
        require(shelf["product_id"] in product_ids, f"Unknown product in shelf {shelf['shelf_id']}.")
        require(shelf["zone_id"] in zone_ids, f"Unknown zone in shelf {shelf['shelf_id']}.")
        require(shelf["available_quantity"] >= 0, f"Negative quantity in shelf {shelf['shelf_id']}.")
        if shelf["status"] == "empty":
            require(shelf["available_quantity"] == 0, f"Empty shelf {shelf['shelf_id']} must have zero quantity.")

    for path in paths:
        require(path["start_zone_id"] in zone_ids, f"Unknown start zone in path {path['path_id']}.")
        require(path["end_zone_id"] in zone_ids, f"Unknown end zone in path {path['path_id']}.")
        require(path["distance_meters"] > 0, f"Path {path['path_id']} must have positive distance.")

    for robot in robots:
        require(robot["current_zone_id"] in zone_ids, f"Unknown zone for robot {robot['robot_id']}.")
        require(0 <= robot["battery_level"] <= 100, f"Invalid battery for robot {robot['robot_id']}.")
        require(robot["maximum_load_kg"] > 0, f"Invalid maximum load for robot {robot['robot_id']}.")
        require(0 <= robot["current_load_kg"] <= robot["maximum_load_kg"], f"Invalid current load for robot {robot['robot_id']}.")

    for order in orders:
        require(order["product_id"] in product_ids, f"Unknown product in order {order['order_id']}.")
        require(order["shelf_id"] in shelf_ids, f"Unknown shelf in order {order['order_id']}.")
        require(order["quantity"] > 0, f"Invalid quantity in order {order['order_id']}.")
        require(order["total_weight_kg"] > 0, f"Invalid weight in order {order['order_id']}.")

    for scenario in scenarios:
        require(scenario["order_id"] in order_ids, f"Unknown order in scenario {scenario['scenario_id']}.")
        if "failed_robot_id" in scenario:
            require(scenario["failed_robot_id"] in robot_ids, f"Unknown failed robot in scenario {scenario['scenario_id']}.")
        if "expected_replacement_robot_id" in scenario:
            require(scenario["expected_replacement_robot_id"] in robot_ids, f"Unknown replacement robot in scenario {scenario['scenario_id']}.")

    history_path = MOCK_DIR / "historical_orders.csv"
    with history_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    require(len(rows) >= 168, "Historical order data must contain at least seven days of hourly records.")
    require(all(int(row["order_count"]) >= 0 for row in rows), "Historical order counts must be non-negative.")

    print("Mock data validation passed.")
    print(f"Products: {len(products)}")
    print(f"Shelves: {len(shelves)}")
    print(f"Zones: {len(zones)}")
    print(f"Paths: {len(paths)}")
    print(f"Robots: {len(robots)}")
    print(f"Orders: {len(orders)}")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Historical rows: {len(rows)}")


if __name__ == "__main__":
    main()
