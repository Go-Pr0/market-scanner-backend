from pydantic import BaseModel, Field
from typing import List

class FullyDilutedCoin(BaseModel):
    market_cap_rank: int = Field(..., description="Rank by market capitalization")
    id: str = Field(..., description="CoinGecko coin identifier")
    symbol: str = Field(..., description="Coin symbol")
    circulating_supply: float = Field(..., description="Current circulating supply of the coin")
    max_supply: float = Field(..., description="Maximum supply of the coin")
    fd_pct: float = Field(..., description="Percentage of coins in circulation relative to max supply")

class FullyDilutedResponse(BaseModel):
    coins: List[FullyDilutedCoin]

class TradingPairStats(BaseModel):
    symbol: str = Field(..., description="Trading pair symbol")
    open_24h: float = Field(..., description="Opening price 24 hours ago")
    close_current: float = Field(..., description="Current/latest price")
    high_24h: float = Field(..., description="Highest price in 24 hours")
    low_24h: float = Field(..., description="Lowest price in 24 hours")
    price_change: float = Field(..., description="Price change in absolute terms")
    price_change_percent: float = Field(..., description="Price change percentage")
    volume_24h: float = Field(..., description="24-hour trading volume")
    last_updated: str = Field(..., description="Last update timestamp")

class MarketAnalysisResponse(BaseModel):
    top_gainers: List[TradingPairStats] = Field(..., description="Top 10 gaining trading pairs")
    top_losers: List[TradingPairStats] = Field(..., description="Top 10 losing trading pairs")
    most_active: List[TradingPairStats] = Field(..., description="Top 10 most active trading pairs by volume")
    last_updated: float = Field(..., description="Cache last update timestamp") 