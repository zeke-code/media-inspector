from fastapi import FastAPI

from app.routers import health, images

app = FastAPI()
app.include_router(health.router)
app.include_router(images.router)
