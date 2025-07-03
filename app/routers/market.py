from fastapi import APIRouter, HTTPException

from app.services.fully_diluted_service import get_cached_coins_by_threshold
from app.services.market_analysis_service import get_cached_market_analysis
from app.models.market import MarketAnalysisResponse
# Note: Response model dynamic, so no explicit Pydantic model import

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/fully_diluted/{threshold}")
async def fully_diluted_threshold(threshold: int):
    """Return coins whose fully-diluted percentage is >= `threshold`.

    `threshold` must be an integer multiple of 5 between 0 and 100.
    """
    if threshold not in range(0, 101, 5):
        raise HTTPException(status_code=400, detail="Threshold must be 0, 5, 10, …, 100")

    try:
        coins = get_cached_coins_by_threshold(threshold)
    except ValueError as exc:
        # Should not happen due to earlier validation, but guard anyway
        raise HTTPException(status_code=400, detail=str(exc))

    return {"threshold": threshold, "coins": coins}

@router.get("/analysis", response_model=MarketAnalysisResponse)
async def get_market_analysis():
    """Get market analysis with top 10 gainers, losers, and most active trading pairs."""
    try:
        analysis = get_cached_market_analysis()
        return analysis
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving market analysis: {str(exc)}")

@router.get("/gainers")
async def get_top_gainers():
    """Get top 10 gaining trading pairs for the day."""
    try:
        analysis = get_cached_market_analysis()
        return {"top_gainers": analysis["top_gainers"], "last_updated": analysis["last_updated"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving top gainers: {str(exc)}")

@router.get("/losers")
async def get_top_losers():
    """Get top 10 losing trading pairs for the day."""
    try:
        analysis = get_cached_market_analysis()
        return {"top_losers": analysis["top_losers"], "last_updated": analysis["last_updated"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving top losers: {str(exc)}")

@router.get("/most_active")
async def get_most_active():
    """Get top 10 most active trading pairs by volume in the last 24 hours."""
    try:
        analysis = get_cached_market_analysis()
        return {"most_active": analysis["most_active"], "last_updated": analysis["last_updated"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error retrieving most active: {str(exc)}") 