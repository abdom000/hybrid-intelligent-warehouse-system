from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from hybrid_warehouse.schemas import ShelfStatus
from hybrid_warehouse.shelf_recognition import (
    ShelfRecognitionService,
    StaticShelfPredictor,
    load_manifest,
    validate_image,
)


def create_image(path: Path, size: tuple[int, int] = (64, 64)) -> Path:
    image = Image.new("RGB", size, "white")
    image.save(path, format="JPEG")
    return path


def test_load_manifest_reads_all_records() -> None:
    records = load_manifest("data/mock/shelf_images/manifest.json")

    assert len(records) == 5
    assert records[0].shelf_id == "S1"


def test_validate_image_accepts_valid_jpeg(tmp_path: Path) -> None:
    image_path = create_image(tmp_path / "shelf.jpg")

    assert validate_image(image_path) == image_path


def test_validate_image_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_image(tmp_path / "missing.jpg")


def test_service_returns_prediction_schema(tmp_path: Path) -> None:
    image_path = create_image(tmp_path / "shelf.jpg")
    predictor = StaticShelfPredictor(
        status=ShelfStatus.NORMAL,
        confidence=0.92,
    )
    service = ShelfRecognitionService(predictor)

    result = service.predict(
        shelf_id="S1",
        image_path=image_path,
    )

    assert result.status == "normal"
    assert result.confidence == 0.92
    assert result.requires_manual_review is False


def test_low_confidence_requires_manual_review(tmp_path: Path) -> None:
    image_path = create_image(tmp_path / "shelf.jpg")
    predictor = StaticShelfPredictor(
        status=ShelfStatus.LOW_STOCK,
        confidence=0.40,
    )
    service = ShelfRecognitionService(predictor)

    result = service.predict(
        shelf_id="S2",
        image_path=image_path,
    )

    assert result.requires_manual_review is True


def test_unavailable_image_result_is_unknown() -> None:
    predictor = StaticShelfPredictor(
        status=ShelfStatus.NORMAL,
        confidence=0.90,
    )
    service = ShelfRecognitionService(predictor)

    result = service.unavailable_image_result(shelf_id="S5")

    assert result.status == "unknown"
    assert result.confidence == 0.0
    assert result.requires_manual_review is True
