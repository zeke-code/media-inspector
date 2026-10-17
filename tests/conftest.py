from collections.abc import Callable, Iterator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def image_bytes() -> Callable[..., bytes]:
    """Create real image uploads in memory, without checked-in binary fixtures."""

    def make_image(
        image_format: str = "PNG",
        size: tuple[int, int] = (32, 24),
        mode: str = "RGB",
    ) -> bytes:
        with BytesIO() as buffer, Image.new(mode, size) as image:
            image.save(buffer, format=image_format)
            return buffer.getvalue()

    return make_image
