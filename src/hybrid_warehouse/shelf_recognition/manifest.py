from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from hybrid_warehouse.schemas import ShelfImageManifestItem


def load_manifest(path: str | Path) -> list[ShelfImageManifestItem]:
    manifest_path = Path(path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Shelf image manifest not found: {manifest_path}")

    raw_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Shelf image manifest root must be a list.")

    adapter = TypeAdapter(list[ShelfImageManifestItem])
    return adapter.validate_python(raw_data)
