from fastapi import APIRouter
from datetime import datetime
from app.models.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])

@router.get("/", include_in_schema=False)
async def root():
    """Root path to verify service is running."""
    return {"message": f"{settings.app_name} is running"}

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="API is running successfully",
        timestamp=datetime.now(),
        version=settings.version,
    )

@router.get("/api/status")
async def get_status():
    """Return basic information about the service."""
    return {
        "service": settings.app_name,
        "status": "active",
        "version": settings.version,
        "endpoints": [
            "/", 
            "/health", 
            "/api/status", 
            "/api/market/fully_diluted/{threshold}",
            "/api/market/analysis",
            "/api/market/gainers",
            "/api/market/losers",
            "/api/market/most_active"
        ],
    } 