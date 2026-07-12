from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.schemas import (  # noqa: E402
    HistoricalOrderRecord,
    Order,
    Product,
    Robot,
    Scenario,
    Shelf,
    ShelfImageManifestItem,
    WarehousePath,
    WarehouseZone,
)

MOCK_DIR = PROJECT_ROOT / "data" / "mock"


def load_json(filename: str):
    with (MOCK_DIR / filename).open(encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    products = [Product.model_validate(item) for item in load_json("products.json")]
    zones = [WarehouseZone.model_validate(item) for item in load_json("zones.json")]
    paths = [
        WarehousePath.model_validate(item)
        for item in load_json("warehouse_paths.json")
    ]
    shelves = [Shelf.model_validate(item) for item in load_json("shelves.json")]
    robots = [Robot.model_validate(item) for item in load_json("robots.json")]
    orders = [Order.model_validate(item) for item in load_json("orders.json")]
    scenario_adapter = TypeAdapter(Scenario)
    scenarios = [
        scenario_adapter.validate_python(item)
        for item in load_json("scenarios.json")
    ]
    shelf_images = [
        ShelfImageManifestItem.model_validate(item)
        for item in load_json("shelf_images/manifest.json")
    ]

    with (MOCK_DIR / "historical_orders.csv").open(
        encoding="utf-8",
        newline="",
    ) as file:
        historical_orders = [
            HistoricalOrderRecord.model_validate(row)
            for row in csv.DictReader(file)
        ]

    print("Shared schema validation passed.")
    print(f"Products: {len(products)}")
    print(f"Zones: {len(zones)}")
    print(f"Paths: {len(paths)}")
    print(f"Shelves: {len(shelves)}")
    print(f"Robots: {len(robots)}")
    print(f"Orders: {len(orders)}")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Shelf image records: {len(shelf_images)}")
    print(f"Historical rows: {len(historical_orders)}")


if __name__ == "__main__":
    main()
