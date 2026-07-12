from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ShelfImageError(ValueError):
    pass


def validate_image(path: str | Path) -> Path:
    image_path = Path(path)

    if not image_path.exists():
        raise FileNotFoundError(f"Shelf image not found: {image_path}")

    if not image_path.is_file():
        raise ShelfImageError(f"Shelf image path is not a file: {image_path}")

    try:
        with Image.open(image_path) as image:
            image.verify()

        with Image.open(image_path) as image:
            image_format = image.format
            width, height = image.size

    except UnidentifiedImageError as error:
        raise ShelfImageError(f"Invalid image file: {image_path}") from error

    if image_format not in SUPPORTED_FORMATS:
        raise ShelfImageError(
            f"Unsupported image format {image_format!r}. "
            f"Supported formats: {sorted(SUPPORTED_FORMATS)}"
        )

    if width < 32 or height < 32:
        raise ShelfImageError(
            f"Image is too small: {width}x{height}. Minimum size is 32x32."
        )

    return image_path
