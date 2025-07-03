"""
Data fetcher module for retrieving and processing Bybit market data.
"""
import asyncio
import pandas as pd
import logging
import os
from datetime import datetime, timedelta, timezone
import time

from database.db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_fetcher')

class DataFetcher:
    def __init__(self, api_client, db_manager, timeframe, target_candles=None):
        """
        Initialize the data fetcher.
        
        Args:
            api_client: BybitClient instance
            db_manager: DatabaseManager instance
            timeframe: Kline timeframe (e.g., "15" for 15 minutes)
            target_candles: Target number of candles to fetch (default: None)
        """
        self.api_client = api_client
        self.db_manager = db_manager
        self.timeframe = timeframe
        self.target_candles = target_candles
    
    async def fetch_and_store_data(self, symbol, force_full_fetch=False):
        """
        Fetch data for a symbol and store it in the database.
        
        - If no data exists, it performs an initial historical fetch for `target_candles`.
        - If data exists, it checks if the time for a new candle has arrived and fetches only new candles.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            force_full_fetch: If True, fetch the full target_candles amount regardless of existing data
            
        Returns:
            tuple: (Number of new candles stored, Error message if any)
        """
        latest_timestamp_ms = await self.db_manager.get_latest_candle_timestamp(symbol)
        
        candles_to_fetch = None
        start_time = None
        
        # Case 1: No data exists for the symbol, or a full fetch is forced.
        if force_full_fetch or not latest_timestamp_ms:
            if force_full_fetch:
                logger.info(f"Forcing full historical fetch for {symbol} ({self.target_candles} candles)")
            else:
                logger.info(f"No existing data for {symbol}, fetching initial history ({self.target_candles} candles)")
            
            candles_to_fetch = self.target_candles

        # Case 2: Data exists. Check if it's time for a new candle.
        else:
            latest_dt = datetime.fromtimestamp(latest_timestamp_ms / 1000, tz=timezone.utc)
            
            try:
                timeframe_minutes = int(self.timeframe)
            except ValueError:
                logger.error(f"Invalid timeframe format: {self.timeframe}. Must be an integer.")
                # Default to 15 minutes if timeframe is invalid
                timeframe_minutes = 15

            # Calculate the start time of the next expected candle
            next_candle_start_dt = latest_dt + timedelta(minutes=timeframe_minutes)

            # Check if the next candle is due
            if datetime.now(timezone.utc) >= next_candle_start_dt:
                logger.info(f"New candle expected for {symbol}. Last candle at {latest_dt}, next at {next_candle_start_dt}.")
                # Fetch all candles since the last one we have.
                start_time = int(next_candle_start_dt.timestamp() * 1000)
            else:
                # Not time for a new candle yet, so do nothing.
                logger.debug(f"No new candle expected for {symbol} yet. Last candle at {latest_dt}, next at {next_candle_start_dt}.")
                return 0, None

        # Fetch data from API only if we have something to do
        df, error = await self.api_client.fetch_kline_data(
            symbol, 
            self.timeframe, 
            start_time=start_time,
            target_candles=candles_to_fetch
        )
        
        if error:
            logger.error(f"Error fetching data for {symbol}: {error}")
            return 0, error
        
        if df is None or df.empty:
            if start_time:
                 logger.info(f"No new data was available for {symbol} after the expected time.")
            else:
                 logger.info(f"No initial data found for {symbol}")
            return 0, None
        
        logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
        
        # Store in database
        stored_count = await self.db_manager.save_candles(symbol, df)
        
        return stored_count, None
