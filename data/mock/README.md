# Mock Data

This directory contains deterministic mock data for development, integration, and testing.

## Files

- `products.json`: warehouse products.
- `shelves.json`: shelf state and inventory.
- `zones.json`: warehouse graph nodes.
- `warehouse_paths.json`: directed graph edges.
- `robots.json`: robot operational states.
- `orders.json`: assignment requests.
- `historical_orders.csv`: hourly order history for forecasting.
- `scenarios.json`: expected integration scenarios.
- `shelf_images/manifest.json`: expected shelf-image references.

## Important Notes

- All identifiers follow `docs/data_contracts.md`.
- Timestamps use ISO 8601 UTC.
- The shelf-image files are intentionally not included yet. The manifest defines the expected names and labels.
- Run `python scripts/validate_mock_data.py` from the project root to validate referential integrity and core constraints.
