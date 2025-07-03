"""
Market analysis service for calculating top gainers, losers, and most active trading pairs.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from threading import Lock

from app.bybit_data_fetcher.database.db_manager import DatabaseManager
from app.bybit_data_fetcher.config.settings import DATABASE_PATH
from app.bybit_data_fetcher.config.candle_monitor_config import get_trading_pairs

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('market_analysis_service')

# Cache variables
_cached_gainers: List[Dict[str, Any]] = []
_cached_losers: List[Dict[str, Any]] = []
_cached_most_active: List[Dict[str, Any]] = []
_last_update: float = 0.0
_cache_lock: Lock = Lock()

class MarketAnalysisService:
    def __init__(self):
        self.db_manager = None
        
    async def connect(self):
        """Connect to the database."""
        if self.db_manager is None:
            self.db_manager = DatabaseManager(DATABASE_PATH)
            await self.db_manager.connect()
    
    async def close(self):
        """Close the database connection."""
        if self.db_manager:
            await self.db_manager.close()
            self.db_manager = None
    
    async def calculate_24h_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Calculate 24-hour statistics for a given symbol."""
        try:
            # Get current time and 24 hours ago
            now = datetime.now(timezone.utc)
            twenty_four_hours_ago = now - timedelta(hours=24)
            
            # Convert to milliseconds for database query
            end_timestamp = int(now.timestamp() * 1000)
            start_timestamp = int(twenty_four_hours_ago.timestamp() * 1000)
            
            # Get candles for the last 24 hours
            df = await self.db_manager.get_candle_range(
                symbol, 
                start_timestamp=start_timestamp, 
                end_timestamp=end_timestamp,
                limit=100  # 24 hours = 96 15-minute candles max
            )
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # Sort by timestamp to ensure correct order
            df = df.sort_values('timestamp')
            
            # Get the first (oldest) and last (newest) candles
            first_candle = df.iloc[0]
            last_candle = df.iloc[-1]
            
            # Calculate 24-hour change
            open_price = first_candle['open']
            close_price = last_candle['close']
            high_price = df['high'].max()
            low_price = df['low'].min()
            
            price_change = close_price - open_price
            price_change_percent = (price_change / open_price) * 100 if open_price != 0 else 0
            
            # Calculate volume (sum of all volume in 24h)
            total_volume = df['volume'].sum()
            
            return {
                'symbol': symbol,
                'open_24h': float(open_price),
                'close_current': float(close_price),
                'high_24h': float(high_price),
                'low_24h': float(low_price),
                'price_change': float(price_change),
                'price_change_percent': float(price_change_percent),
                'volume_24h': float(total_volume),
                'last_updated': last_candle['timestamp'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating stats for {symbol}: {str(e)}")
            return None
    
    async def get_market_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get market analysis with top gainers, losers, and most active."""
        try:
            # Ensure database connection
            await self.connect()
            
            # Get all trading pairs
            trading_pairs = get_trading_pairs()
            
            # Calculate stats for all pairs
            all_stats = []
            tasks = []
            
            for symbol in trading_pairs:
                tasks.append(self.calculate_24h_stats(symbol))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {trading_pairs[i]}: {result}")
                elif result is not None:
                    all_stats.append(result)
            
            # Filter out None results
            valid_stats = [stat for stat in all_stats if stat is not None]
            
            if not valid_stats:
                logger.warning("No valid market data available")
                return {
                    'top_gainers': [],
                    'top_losers': [],
                    'most_active': []
                }
            
            # Sort for top gainers (highest price change %)
            top_gainers = sorted(valid_stats, key=lambda x: x['price_change_percent'], reverse=True)[:5]
            
            # Sort for top losers (lowest price change %)
            top_losers = sorted(valid_stats, key=lambda x: x['price_change_percent'])[:5]
            
            # Sort for most active (highest volume)
            most_active = sorted(valid_stats, key=lambda x: x['volume_24h'], reverse=True)[:5]
            
            return {
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'most_active': most_active
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return {
                'top_gainers': [],
                'top_losers': [],
                'most_active': []
            }

# Global service instance
market_analysis_service = MarketAnalysisService()

async def update_market_analysis_cache() -> None:
    """Update the cached market analysis data."""
    global _cached_gainers, _cached_losers, _cached_most_active, _last_update
    
    with _cache_lock:
        try:
            analysis = await market_analysis_service.get_market_analysis()
            
            _cached_gainers = analysis['top_gainers']
            _cached_losers = analysis['top_losers']
            _cached_most_active = analysis['most_active']
            _last_update = datetime.now().timestamp()
            
            logger.info(f"Market analysis cache updated with {len(_cached_gainers)} gainers, "
                       f"{len(_cached_losers)} losers, {len(_cached_most_active)} most active")
            
        except Exception as exc:
            logger.error(f"Failed to refresh market analysis cache: {exc}")

def get_cached_market_analysis() -> Dict[str, List[Dict[str, Any]]]:
    """Return cached market analysis data."""
    return {
        'top_gainers': list(_cached_gainers),
        'top_losers': list(_cached_losers),
        'most_active': list(_cached_most_active),
        'last_updated': _last_update
    } 