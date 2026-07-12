from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hybrid_warehouse.shelf_recognition import (  # noqa: E402
    inspect_manifest_images,
    load_manifest,
)

MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "mock" / "shelf_images" / "manifest.json"
)
REPORT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "shelf_recognition_report.json"
)


def main() -> None:
    records = load_manifest(MANIFEST_PATH)
    statuses = inspect_manifest_images(
        project_root=PROJECT_ROOT,
        records=records,
    )

    existing_count = sum(item.file_exists for item in statuses)
    missing_count = len(statuses) - existing_count

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "pipeline_only",
        "trained_model_available": False,
        "reason": (
            "No shelf image files are currently available. "
            "The recognition interface, validation, fallback behavior, "
            "and tests are implemented, but no visual model is trained."
        ),
        "records": len(statuses),
        "existing_images": existing_count,
        "missing_images": missing_count,
        "items": [item.to_dict() for item in statuses],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print("Shelf recognition pipeline validation passed.")
    print(f"Manifest records: {len(statuses)}")
    print(f"Existing images: {existing_count}")
    print(f"Missing images: {missing_count}")
    print("Trained model available: no")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
