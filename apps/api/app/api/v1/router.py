from fastapi import APIRouter
from app.api.v1.endpoints import analyze, health, screenshots

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(analyze.router, tags=["analysis"])
api_router.include_router(screenshots.router, tags=["screenshots"])
