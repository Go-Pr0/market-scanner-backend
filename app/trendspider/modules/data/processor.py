import asyncio
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Sequence

from ... import config
from ... import symbols
from .fetcher import fetch_kline_data_async, convert_timeframe_to_minutes
from ..calculation.ema import calculate_all_emas

# Setup logging
logger = logging.getLogger(__name__)

async def process_symbol_batch(symbols: List[str], interval: str = "240", periods: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    Process a batch of symbols concurrently with timeframe conversion
    
    Args:
        symbols: List of trading symbols
        interval: Timeframe interval
        periods: List of EMA periods to calculate
        
    Returns:
        List of dictionaries with processed symbol data
    """
    # Use default periods if none provided
    if periods is None:
        periods = config.EMA_PERIODS
        
    # Get maximum period (for determining how many candles to fetch)
    max_period = max(periods) if periods else 200
    
    # Convert interval to minutes for logging
    requested_timeframe_minutes = convert_timeframe_to_minutes(interval)
    
    # Create tasks for each symbol
    tasks = []
    for symbol in symbols:
        task = fetch_kline_data_async(None, symbol, interval, max_period)
        tasks.append(task)
        
    # Gather results
    results = await asyncio.gather(*tasks)
    
    # Process each result to calculate EMAs and percentages
    processed_results = []
    
    for result_tuple in results:
        result, df = result_tuple
        
        # Skip if there was an error fetching data
        if not result.get("success", False):
            processed_results.append(result)
            continue
            
        symbol = result["symbol"]
        
        try:
            # Initialize EMA storage
            result["emas"] = {}
            result["percent_from_ema"] = {}
            
            # Get current price
            current_price = result["price"]
            
            # Skip if no DataFrame was returned (shouldn't happen if success=True, but safety check)
            if df is None or df.empty:
                logger.warning(f"No data available for EMA calculation for {symbol}")
                result["success"] = False
                result["error"] = "No candle data available for EMA calculation"
                processed_results.append(result)
                continue
            
            # Check if we have enough data for the largest EMA period
            if len(df) < max_period:
                logger.warning(f"Insufficient data for {max_period}-period EMA calculation for {symbol}. "
                             f"Have {len(df)} candles, need {max_period}")
                # We'll still try to calculate what we can
            
            # Calculate all EMAs at once
            emas_dict = calculate_all_emas(df, periods)
            
            # Process each requested EMA period
            for period in periods:
                if period not in emas_dict:
                    logger.warning(f"Could not calculate {period}-period EMA for {symbol}")
                    continue
                
                # Get the most recent EMA value
                latest_ema = float(emas_dict[period].iloc[-1])
                logger.debug(f"Calculated {period}-period EMA for {symbol}: {latest_ema}")
                
                # Calculate percentage difference
                percent_diff = ((current_price - latest_ema) / latest_ema) * 100
                
                # Store in result
                result["emas"][str(period)] = latest_ema
                result["percent_from_ema"][str(period)] = percent_diff
                
            # Add to processed results
            processed_results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            result["success"] = False
            result["error"] = str(e)
            processed_results.append(result)
            
    return processed_results

async def get_emas_for_all_symbols(symbols_list: Optional[List[str]] = None, interval: str = "240", 
                                  periods: Optional[List[int]] = None, batch_size: int = 4) -> List[Dict[str, Any]]:
    """
    Get EMAs for all symbols in batches with timeframe conversion
    
    Args:
        symbols_list: List of trading symbols (use default list if None)
        interval: Timeframe interval
        periods: List of EMA periods to calculate
        batch_size: Number of symbols to process in parallel
        
    Returns:
        List of dictionaries with processed symbol data
    """
    # Use default symbols if none provided
    if symbols_list is None:
        symbols_list = symbols.symbols
        
    # Use default periods if none provided
    if periods is None:
        periods = config.EMA_PERIODS
        
    # Use default batch size if invalid
    if batch_size < 1:
        batch_size = config.BATCH_SIZE
        
    # Log timeframe conversion info
    requested_timeframe_minutes = convert_timeframe_to_minutes(interval)
    logger.info(f"Processing {len(symbols_list)} symbols for {requested_timeframe_minutes}m timeframe, "
               f"EMA periods: {periods}")
        
    # Process in batches
    all_results = []
    total_symbols = len(symbols_list)
    
    for i in range(0, total_symbols, batch_size):
        # Get batch of symbols
        batch = symbols_list[i:i+batch_size]
        
        # Log progress
        logger.info(f"Processing batch {i//batch_size + 1}/{(total_symbols+batch_size-1)//batch_size} ({len(batch)} symbols)")
        
        # Process batch
        batch_results = await process_symbol_batch(batch, interval, periods)
        all_results.extend(batch_results)
        
    return all_results 