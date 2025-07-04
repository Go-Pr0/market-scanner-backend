"""
Market data endpoints for the TrendSpider API
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ..core.security import require_auth
from ..services.fully_diluted_service import get_cached_coins_by_threshold
from ..services.market_analysis_service import (
    get_cached_market_analysis, 
    get_cached_gainers, 
    get_cached_losers, 
    get_cached_most_active
)
from ..models.market import TradingPairStats, MarketAnalysisResponse

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/fully_diluted/{threshold}")
async def get_fully_diluted_symbols(threshold: int, _: str = Depends(require_auth)):
    """
    Get coins with fully diluted valuation percentage above the threshold
    
    Args:
        threshold: Minimum fully diluted percentage (0-100)
        
    Returns:
        List of coins meeting the criteria
    """
    try:
        # Validate threshold range
        if threshold not in range(0, 101, 5):
            raise HTTPException(status_code=400, detail="Threshold must be 0, 5, 10, ..., 100")
        
        coins = get_cached_coins_by_threshold(threshold)
        
        return {
            "threshold": threshold,
            "coins": coins
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis", response_model=MarketAnalysisResponse)
async def get_market_analysis(_: str = Depends(require_auth)):
    """
    Get complete market analysis including top gainers, losers, and most active pairs
    
    Returns:
        Market analysis data
    """
    try:
        analysis = get_cached_market_analysis()
        
        return MarketAnalysisResponse(
            top_gainers=analysis['top_gainers'],
            top_losers=analysis['top_losers'],
            most_active=analysis['most_active'],
            last_updated=analysis['last_updated']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gainers", response_model=List[TradingPairStats])
async def get_top_gainers(_: str = Depends(require_auth)):
    """
    Get top gaining trading pairs in the last 24 hours
    
    Returns:
        List of top gaining pairs
    """
    try:
        gainers = get_cached_gainers()
        return gainers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/losers", response_model=List[TradingPairStats])
async def get_top_losers(_: str = Depends(require_auth)):
    """
    Get top losing trading pairs in the last 24 hours
    
    Returns:
        List of top losing pairs
    """
    try:
        losers = get_cached_losers()
        return losers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most_active", response_model=List[TradingPairStats])
async def get_most_active(_: str = Depends(require_auth)):
    """
    Get most active trading pairs by volume in the last 24 hours
    
    Returns:
        List of most active pairs
    """
    try:
        most_active = get_cached_most_active()
        return most_active
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 