from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("image_format", "mode"),
    [
        ("PNG", "RGB"),
        ("PNG", "RGBA"),
        ("PNG", "L"),
        ("JPEG", "RGB"),
        ("JPEG", "L"),
        ("JPEG", "CMYK"),
    ],
)
def test_analyze_returns_image_properties(
    client: TestClient,
    image_bytes: Callable[..., bytes],
    image_format: str,
    mode: str,
):
    content = image_bytes(image_format=image_format, mode=mode)

    response = client.post(
        "/analyze",
        files={"file": ("image", content, f"image/{image_format.lower()}")},
    )

    assert response.status_code == 200
    properties = response.json()
    processing_ms = properties.pop("processing_ms")
    assert isinstance(processing_ms, (int, float))
    assert processing_ms >= 0
    assert properties == {
        "format": image_format,
        "width": 32,
        "height": 24,
        "size_bytes": len(content),
        "mode": mode,
    }


def test_analyze_detects_format_from_content(
    client: TestClient, image_bytes: Callable[..., bytes]
):
    response = client.post(
        "/analyze",
        files={"file": ("misleading.jpg", image_bytes(), "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["format"] == "PNG"


@pytest.mark.parametrize("content", [b"", b"not an image", b"\x89PNG\r\n\x1a\n"])
def test_analyze_rejects_unreadable_images(client: TestClient, content: bytes):
    response = client.post(
        "/analyze", files={"file": ("image.png", content, "image/png")}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsupported file type"}


def test_analyze_requires_a_file(client: TestClient):
    response = client.post("/analyze")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


def test_analyze_requires_the_file_field(
    client: TestClient, image_bytes: Callable[..., bytes]
):
    response = client.post(
        "/analyze", files={"image": ("image.png", image_bytes(), "image/png")}
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


def test_analyze_rejects_a_text_field(client: TestClient):
    response = client.post("/analyze", data={"file": "image.png"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


@pytest.mark.parametrize(
    ("size_bytes", "status_code"),
    [(4_999_999, 200), (5_000_000, 413), (5_000_001, 413)],
)
def test_analyze_enforces_the_exclusive_byte_limit(
    client: TestClient,
    image_bytes: Callable[..., bytes],
    size_bytes: int,
    status_code: int,
):
    # PNG readers ignore trailing bytes; padding controls the actual upload size.
    content = image_bytes().ljust(size_bytes, b"\0")

    response = client.post(
        "/analyze", files={"file": ("image.png", content, "image/png")}
    )

    assert response.status_code == status_code
    if status_code == 200:
        assert response.json()["size_bytes"] == size_bytes
    else:
        assert response.json() == {"detail": "Image must be smaller than 5 MB"}


@pytest.mark.parametrize(
    ("width", "status_code"), [(4_999, 200), (5_000, 422), (5_001, 422)]
)
def test_analyze_enforces_the_exclusive_pixel_limit(
    client: TestClient,
    image_bytes: Callable[..., bytes],
    width: int,
    status_code: int,
):
    # One-bit PNGs exercise real image dimensions with small encoded uploads.
    content = image_bytes(size=(width, 4_000), mode="1")

    response = client.post(
        "/analyze", files={"file": ("image.png", content, "image/png")}
    )

    assert response.status_code == status_code
    if status_code == 200:
        assert response.json()["width"] == width
        assert response.json()["height"] == 4_000
    else:
        assert response.json() == {"detail": "Image must be smaller than 20 megapixels"}


def test_analyze_checks_image_type_before_size(client: TestClient):
    response = client.post(
        "/analyze",
        files={"file": ("invalid.png", b"x" * 5_000_000, "image/png")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsupported file type"}


def test_analyze_checks_dimensions_before_size(
    client: TestClient, image_bytes: Callable[..., bytes]
):
    content = image_bytes(size=(5_000, 4_000), mode="1").ljust(5_000_000, b"\0")

    response = client.post(
        "/analyze", files={"file": ("image.png", content, "image/png")}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Image must be smaller than 20 megapixels"}


@pytest.mark.parametrize("image_format", ["GIF", "BMP"])
def test_analyze_rejects_unsupported_image_formats(
    client: TestClient, image_bytes: Callable[..., bytes], image_format: str
):
    content = image_bytes(image_format=image_format)

    response = client.post(
        "/analyze",
        files={"file": ("image", content, "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Image format not valid, must be JPEG or PNG"}
