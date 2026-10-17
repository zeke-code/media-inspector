from pydantic import BaseModel, Field
from typing import Literal

class ImageProperties(BaseModel):
    format: Literal["JPEG", "PNG"]
    width: int
    height: int
    size_bytes: int = Field(lt=5000000)
    mode: str
    processing_ms: float
