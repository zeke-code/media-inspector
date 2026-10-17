from fastapi import APIRouter, UploadFile

from app.schemas.images import ImageProperties
from app.services import images

router = APIRouter(tags=["images"])


@router.post("/analyze")
async def analyze_image(file: UploadFile) -> ImageProperties:
    return images.analyze_image(file.file, file.size)
