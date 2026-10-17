import time
import logging

from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError
from .models import ImageProperties


app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_image(file: UploadFile):
    start = time.perf_counter()

    MAX_PIXELS = 20_000_000
    MAX_BYTES = 5_000_000

    try:
        image = Image.open(file.file)
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=422,
            detail="Unsupported file type"
        )

    if image.width * image.height >= MAX_PIXELS:
        raise HTTPException(
            status_code=422,
            detail="Image must be smaller than 20 megapixels"
        )

    if file.size >= MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image must be smaller than 5 MB"
        )

    return ImageProperties(
        format=image.format,
        width=image.width,
        height=image.height,
        size_bytes=file.size,
        mode=image.mode,
        processing_ms=round(
            (time.perf_counter() - start) * 1000, 2
        )
    
    )
