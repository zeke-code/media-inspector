from collections.abc import Callable
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.images import analyze_image


def test_analyze_reports_rounded_milliseconds(image_bytes: Callable[..., bytes]):
    content = image_bytes()

    with (
        BytesIO(content) as file,
        patch("app.services.images.time.perf_counter", side_effect=[10, 10.012346]),
    ):
        properties = analyze_image(file, len(content))

    assert properties.processing_ms == 12.35


def test_analyze_can_be_used_without_an_http_upload(image_bytes: Callable[..., bytes]):
    content = image_bytes(image_format="JPEG", size=(80, 60))

    with BytesIO(content) as file:
        properties = analyze_image(file, len(content))

    assert properties.model_dump(exclude={"processing_ms"}) == {
        "format": "JPEG",
        "width": 80,
        "height": 60,
        "size_bytes": len(content),
        "mode": "RGB",
    }


def test_analyze_raises_422_for_unreadable_data():
    with (
        BytesIO(b"invalid") as file,
        pytest.raises(HTTPException) as exc_info,
    ):
        analyze_image(file, 7)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Unsupported file type"


def test_analyze_raises_422_at_pixel_limit(image_bytes: Callable[..., bytes]):
    content = image_bytes(size=(5_000, 4_000), mode="1")

    with (
        BytesIO(content) as file,
        pytest.raises(HTTPException) as exc_info,
    ):
        analyze_image(file, len(content))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Image must be smaller than 20 megapixels"


def test_analyze_raises_413_at_byte_limit(image_bytes: Callable[..., bytes]):
    content = image_bytes()

    with (
        BytesIO(content) as file,
        pytest.raises(HTTPException) as exc_info,
    ):
        analyze_image(file, 5_000_000)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Image must be smaller than 5 MB"
