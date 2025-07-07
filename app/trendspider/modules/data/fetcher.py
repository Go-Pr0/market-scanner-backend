import os
import sys
import pandas as pd
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from app.core.config import config as app_config
from ... import config

# Setup logging
logger = logging.getLogger(__name__)

# Database manager will be initialized lazily
db_manager = None

# Timeframe conversion constants
DATABASE_TIMEFRAME_MINUTES = 15  # Database stores 15-minute candles

def get_db_manager():
    """Get or initialize the database manager"""
    global db_manager
    if db_manager is None:
        # Add the modules directory to sys.path to enable imports
        current_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(current_dir, '..', '..', '..')
        modules_dir = os.path.abspath(modules_dir)
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)
        
        # Import and initialize DatabaseManager
        from bybit_data_fetcher.database.db_manager import DatabaseManager
        
        # Initialize database manager using centralized config
        db_manager = DatabaseManager(app_config.BYBIT_DB_PATH)
        logger.info(f"Initialized database manager with path: {app_config.BYBIT_DB_PATH}")
    
    return db_manager

def convert_timeframe_to_minutes(interval: str) -> int:
    """Convert timeframe string to minutes"""
    timeframe_map = {
        "1": 1, "5": 5, "15": 15, "30": 30, "60": 60,
        "120": 120, "240": 240, "360": 360, "720": 720, "1440": 1440
    }
    return timeframe_map.get(interval, 240)  # Default to 4H if unknown

def resample_candles_to_timeframe(df: pd.DataFrame, target_timeframe_minutes: int) -> pd.DataFrame:
    """
    Resample 15-minute candles to target timeframe
    
    Args:
        df: DataFrame with 15-minute candles
        target_timeframe_minutes: Target timeframe in minutes
        
    Returns:
        DataFrame resampled to target timeframe
    """
    if target_timeframe_minutes == DATABASE_TIMEFRAME_MINUTES:
        return df  # No resampling needed
    
    # Set timestamp as index for resampling
    df_copy = df.copy()
    df_copy.set_index('timestamp', inplace=True)
    
    # Calculate resampling frequency
    freq = f'{target_timeframe_minutes}min'
    
    # Resample OHLCV data (removed ema_3200 reference)
    resampled = df_copy.resample(freq).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min', 
        'close': 'last',
        'volume': 'sum',
        'turnover': 'sum'
    }).dropna()
    
    # Reset index to make timestamp a column again
    resampled.reset_index(inplace=True)
    
    logger.debug(f"Resampled {len(df)} 15m candles to {len(resampled)} {target_timeframe_minutes}m candles")
    
    return resampled

async def fetch_kline_data_async(session=None, symbol: str = "", interval: str = "240", max_period: Optional[int] = None) -> Tuple[Dict[str, Any], Optional[pd.DataFrame]]:
    """
    Fetch kline data from local database for a symbol with timeframe conversion
    
    Args:
        session: Unused parameter (kept for compatibility)
        symbol: Trading symbol (e.g., 'BTCUSDT')
        interval: Timeframe interval in minutes or timeframe code
        max_period: Maximum EMA period to calculate (determines how many candles to fetch)
        
    Returns:
        Tuple of (Dictionary with symbol data and EMA calculations, DataFrame with candle data or None)
    """
    try:
        # Convert interval to minutes
        requested_timeframe_minutes = convert_timeframe_to_minutes(interval)
        
        # Determine how many database candles to fetch
        limit = 1000  # Default increased from 500
        if max_period:
            # Calculate how many 15m candles we need for the target timeframe
            candles_per_period = requested_timeframe_minutes // DATABASE_TIMEFRAME_MINUTES
            # Need enough 15m candles to create max_period candles in target timeframe
            required_15m_candles = max_period * candles_per_period
            # Add buffer for EMA calculation warmup
            limit = min(10000, max(1000, required_15m_candles * 2))
            
        start_time = time.time()
        
        # Get database manager and fetch 15-minute data
        db_mgr = get_db_manager()
        
        # Connect to database if not already connected
        if db_mgr.conn is None:
            await db_mgr.connect()
            
        df_15m = await db_mgr.get_latest_candles(symbol, limit)
        
        # Check if we have data
        if df_15m.empty:
            logger.warning(f"No candle data found in database for {symbol}")
            return {
                "symbol": symbol, 
                "success": False,
                "error": "No data available in database",
                "timestamp": datetime.now().isoformat()
            }, None
        
        # Resample to target timeframe if needed
        if requested_timeframe_minutes != DATABASE_TIMEFRAME_MINUTES:
            df = resample_candles_to_timeframe(df_15m, requested_timeframe_minutes)
        else:
            df = df_15m
        
        # Check if we still have data after resampling
        if df.empty:
            logger.warning(f"No data available after resampling to {requested_timeframe_minutes}m for {symbol}")
            return {
                "symbol": symbol, 
                "success": False,
                "error": f"No data available after resampling to {requested_timeframe_minutes}m timeframe",
                "timestamp": datetime.now().isoformat()
            }, None
        
        # Get current price from the most recent candle
        current_price = float(df["close"].iloc[-1])
        current_volume = float(df["volume"].sum())  # Total volume in the period
        
        # Basic info about the symbol
        result = {
            "symbol": symbol,
            "price": current_price,
            "volume": current_volume,
            "success": True,
            "emas": {},  # Will be filled with EMA values
            "percent_from_ema": {},  # Will be filled with % difference values
            "timestamp": datetime.now().isoformat(),
            "timeframe": interval,
            "actual_timeframe_minutes": requested_timeframe_minutes,
            "candles_available": len(df)
        }
        
        # Log processing time
        fetch_time = time.time() - start_time
        logger.debug(f"Fetched {symbol} from database in {fetch_time:.2f}s "
                    f"({len(df_15m)} 15m candles -> {len(df)} {requested_timeframe_minutes}m candles)")
        
        return result, df
            
    except Exception as e:
        logger.error(f"Error fetching data from database for {symbol}: {str(e)}")
        return {
            "symbol": symbol,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, None 