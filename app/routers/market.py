import logging
from fastapi import APIRouter, HTTPException, Depends

from app.services.fully_diluted_service import get_cached_coins_by_threshold
from app.services.market_analysis_service import get_cached_market_analysis
from app.models.market import MarketAnalysisResponse
from app.core.security import require_auth
# Note: Response model dynamic, so no explicit Pydantic model import

router = APIRouter(prefix="/api/market", tags=["market"])
logger = logging.getLogger(__name__)

@router.get("/fully_diluted/{threshold}")
async def fully_diluted_threshold(threshold: int, _: bool = Depends(require_auth)):
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
async def get_market_analysis(_: bool = Depends(require_auth)):
    """Get market analysis with top 10 gainers, losers, and most active trading pairs."""
    try:
        analysis = get_cached_market_analysis()
        if not analysis:
            logger.warning("Market analysis data not yet available.")
            raise HTTPException(status_code=404, detail="Market analysis data is not ready yet. Please try again in a moment.")
        return analysis
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving market analysis: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving market analysis.")

@router.get("/gainers")
async def get_top_gainers(_: bool = Depends(require_auth)):
    """Get top 10 gaining trading pairs for the day."""
    try:
        analysis = get_cached_market_analysis()
        if not analysis or 'top_gainers' not in analysis:
            raise HTTPException(status_code=404, detail="Gainer data not available.")
        return {"top_gainers": analysis["top_gainers"], "last_updated": analysis["last_updated"]}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving top gainers: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving top gainers.")

@router.get("/losers")
async def get_top_losers(_: bool = Depends(require_auth)):
    """Get top 10 losing trading pairs for the day."""
    try:
        analysis = get_cached_market_analysis()
        if not analysis or 'top_losers' not in analysis:
            raise HTTPException(status_code=404, detail="Loser data not available.")
        return {"top_losers": analysis["top_losers"], "last_updated": analysis["last_updated"]}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving top losers: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving top losers.")

@router.get("/most_active")
async def get_most_active(_: bool = Depends(require_auth)):
    """Get top 10 most active trading pairs by volume in the last 24 hours."""
    try:
        analysis = get_cached_market_analysis()
        if not analysis or 'most_active' not in analysis:
            raise HTTPException(status_code=404, detail="Most active data not available.")
        return {"most_active": analysis["most_active"], "last_updated": analysis["last_updated"]}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving most active: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while retrieving most active.") 