"""
Bybit API client for fetching kline (candlestick) data.
"""
import asyncio
import aiohttp
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bybit_client')

class BybitClient:
    def __init__(self, base_url, category="linear"):
        """Initialize the Bybit API client."""
        self.base_url = base_url
        self.category = category
        self.session = None
    
    async def __aenter__(self):
        """Create session for context manager usage."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session for context manager usage."""
        if self.session:
            await self.session.close()
            self.session = None
    

    
    async def fetch_kline_data(self, symbol, interval, start_time=None, end_time=None, target_candles=None):
        """
        Fetch kline data for a symbol.
        
        If start_time is provided without target_candles, it will fetch all candles since start_time (for updates).
        If target_candles is provided, it will fetch that many of the most recent candles.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            interval: Timeframe interval (e.g., "15" for 15 minutes)
            start_time: Optional timestamp to start fetching from (for updates)
            end_time: Optional timestamp to fetch until
            target_candles: Optional target number of candles to fetch (for history)
            
        Returns:
            tuple: (DataFrame of candle data, error message if any)
        """
        created_session = False
        if self.session is None:
            self.session = aiohttp.ClientSession()
            created_session = True

        try:
            if start_time and not target_candles:
                # This is an incremental update, fetch all candles since start_time
                return await self._fetch_incremental_update(symbol, interval, start_time)
            else:
                # This is a historical fetch for a target number of candles
                return await self._fetch_historical_data(symbol, interval, end_time, target_candles)

        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error fetching data for {symbol}: {e}")
            return None, f"Connection error for {symbol}: {e}"
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {str(e)}", exc_info=True)
            return None, f"Error fetching data for {symbol}: {str(e)}"
        finally:
            if created_session and self.session:
                await self.session.close()

    async def _fetch_incremental_update(self, symbol, interval, start_time):
        """Fetch new candles since a given start time."""
        params = {
            "category": self.category,
            "symbol": symbol,
            "interval": interval,
            "start": start_time,
            "limit": 1000  # Max limit, should be enough for updates
        }
        logger.debug(f"Fetching incremental update for {symbol} with params: {params}")

        df, error = await self._make_api_request(params)
        if error:
            return None, error
        
        # API returns newest first, we need to sort by timestamp ascending
        if df is not None and not df.empty:
            df = df.sort_values("timestamp", ascending=True)
            
        return df, None

    async def _fetch_historical_data(self, symbol, interval, end_time, target_candles):
        """Fetch a specific number of historical candles."""
        MAX_CANDLES_PER_REQUEST = 1000
        
        if not target_candles:
            required_candles = MAX_CANDLES_PER_REQUEST
        else:
            required_candles = target_candles
            
        # Correct calculation for chunks needed
        chunks_needed = (required_candles + MAX_CANDLES_PER_REQUEST - 1) // MAX_CANDLES_PER_REQUEST

        all_klines = []
        current_end_time = end_time

        for i in range(chunks_needed):
            limit = min(required_candles - len(all_klines), MAX_CANDLES_PER_REQUEST)
            if limit <= 0:
                break
                
            params = {
                "category": self.category,
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if current_end_time:
                params["end"] = current_end_time
            
            logger.debug(f"Fetching historical chunk {i+1}/{chunks_needed} for {symbol} with params: {params}")
            
            # Make the API request
            df_chunk, error = await self._make_api_request(params)
            
            if error:
                # If one chunk fails, we might still have data from others, but we'll stop.
                logger.error(f"Error fetching historical chunk for {symbol}: {error}")
                break
            
            if df_chunk is None or df_chunk.empty:
                logger.info(f"No more klines received for {symbol} in chunk {i+1}")
                break
            
            # Data from API is newest first. We add it and will sort later.
            # For pagination, we need the timestamp of the OLDEST candle from the chunk.
            all_klines.extend(df_chunk.to_dict('records'))
            
            # Set end time for the next request
            current_end_time = int(df_chunk['timestamp'].min().timestamp() * 1000) - 1

            if len(all_klines) >= required_candles:
                logger.info(f"Sufficient data ({len(all_klines)}) fetched for {symbol}. Stopping.")
                break

            await asyncio.sleep(0.2)

        if not all_klines:
            return pd.DataFrame(), None # Return empty DataFrame, not an error

        # Convert list of dicts back to DataFrame and sort
        final_df = pd.DataFrame(all_klines).sort_values("timestamp", ascending=True).reset_index(drop=True)
        
        if len(final_df) < required_candles:
             logger.warning(f"Could only retrieve {len(final_df)} candles for {symbol}, needed {required_candles}.")

        logger.info(f"Retrieved {len(final_df)} total historical candles for {symbol}")
        return final_df, None

    async def _make_api_request(self, params):
        """Make a single API request and handle response."""
        async with self.session.get(self.base_url, params=params) as response:
            if response.status != 200:
                if response.status in [502, 503, 504]:
                    logger.warning(f"Received {response.status} for {params['symbol']}, retrying after 1 second...")
                    await asyncio.sleep(1)
                    async with self.session.get(self.base_url, params=params) as retry_response:
                        if retry_response.status != 200:
                            return None, f"HTTP error {retry_response.status} for {params['symbol']} after retry"
                        data = await retry_response.json()
                else:
                    return None, f"HTTP error {response.status} for {params['symbol']}"
            else:
                data = await response.json()

        if data.get("retCode") != 0:
            if "rate limit" in data.get("retMsg", "").lower():
                logger.warning(f"Rate limit hit for {params['symbol']}. Retrying after 2 seconds...")
                await asyncio.sleep(2)
                # Simplified retry logic for now
                return None, f"Rate limit hit for {params['symbol']}" 
            return None, f"API Error for {params['symbol']}: {data.get('retMsg', 'Unknown API error')}"

        klines = data.get("result", {}).get("list", [])
        if not klines:
            return pd.DataFrame(), None # No data is not an error

        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
        
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(np.int64), unit="ms")
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = df[col].astype(float)
        
        return df, None
