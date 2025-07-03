import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
import numpy.typing as npt

from ... import config

# Setup logging
logger = logging.getLogger(__name__)

def calculate_ema_tradingview(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate EMA using TradingView's methodology (optimized)
    
    Args:
        df: DataFrame with OHLC data
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    # Use numpy for speed
    close_prices = np.asarray(df['close'].values, dtype=np.float64)
    alpha = 2 / (period + 1)
    
    # Pre-allocate the output array
    ema = np.zeros_like(close_prices)
    
    # Use SMA for the initial value (TradingView approach)
    ema[period-1] = np.mean(close_prices[:period])
    
    # Calculate EMA using vectorized operations where possible
    for i in range(period, len(close_prices)):
        ema[i] = alpha * close_prices[i] + (1 - alpha) * ema[i-1]
        
    # Convert back to pandas Series
    return pd.Series(ema, index=df.index)

def calculate_all_emas(df: pd.DataFrame, periods: Optional[List[int]] = None) -> Dict[int, pd.Series]:
    """
    Calculate multiple EMAs for a single dataframe
    
    Args:
        df: DataFrame with OHLC data
        periods: List of EMA periods to calculate
        
    Returns:
        Dictionary mapping period to EMA Series
    """
    # Use default periods if none provided
    if periods is None:
        periods = config.EMA_PERIODS
        
    if not periods:
        return {}
        
    # Calculate each EMA
    emas = {}
    for period in periods:
        try:
            # Skip if we don't have enough data for this period
            if len(df) < period:
                logger.warning(f"Not enough data for {period} EMA calculation. Need {period}, have {len(df)}")
                continue
                
            # Calculate EMA
            ema = calculate_ema_tradingview(df, period)
            emas[period] = ema
            
        except Exception as e:
            logger.error(f"Error calculating {period} EMA: {str(e)}")
            
    return emas 