from typing import Literal

from pydantic import BaseModel, Field


class ImageProperties(BaseModel):
    format: Literal["JPEG", "PNG"]
    width: int
    height: int
    size_bytes: int = Field(lt=5_000_000)
    mode: str
    processing_ms: float
