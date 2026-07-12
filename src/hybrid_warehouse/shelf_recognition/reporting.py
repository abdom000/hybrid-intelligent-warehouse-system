from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from hybrid_warehouse.schemas import ShelfImageManifestItem


@dataclass(frozen=True)
class ManifestImageStatus:
    image_id: str
    shelf_id: str
    expected_status: str
    declared_available: bool
    file_exists: bool
    relative_path: str

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def inspect_manifest_images(
    *,
    project_root: str | Path,
    records: list[ShelfImageManifestItem],
) -> list[ManifestImageStatus]:
    root = Path(project_root)

    return [
        ManifestImageStatus(
            image_id=record.image_id,
            shelf_id=record.shelf_id,
            expected_status=str(record.expected_status),
            declared_available=record.available,
            file_exists=(root / record.relative_path).is_file(),
            relative_path=record.relative_path,
        )
        for record in records
    ]
