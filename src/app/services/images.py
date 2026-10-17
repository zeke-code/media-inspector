import time
from typing import BinaryIO

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from app.schemas.images import ImageProperties

MAX_PIXELS = 20_000_000
MAX_BYTES = 5_000_000


def analyze_image(file: BinaryIO, size_bytes: int) -> ImageProperties:
    """Read image metadata using the byte count supplied by the upload parser."""
    start = time.perf_counter()

    try:
        image = Image.open(file)
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=422, detail="Unsupported file type") from exc

    if image.width * image.height >= MAX_PIXELS:
        raise HTTPException(
            status_code=422, detail="Image must be smaller than 20 megapixels"
        )

    if image.format not in ["JPEG", "PNG"]:
        raise HTTPException(
            status_code=422, detail="Image format not valid, must be JPEG or PNG"
        )

    if size_bytes >= MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image must be smaller than 5 MB")

    return ImageProperties(
        format=image.format,
        width=image.width,
        height=image.height,
        size_bytes=size_bytes,
        mode=image.mode,
        processing_ms=round((time.perf_counter() - start) * 1000, 2),
    )
