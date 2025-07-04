"""
Bybit candle monitor service for running the data fetcher as a background task.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the bybit_data_fetcher to the Python path
current_dir = Path(__file__).parent
bybit_fetcher_path = current_dir.parent / "bybit_data_fetcher"
sys.path.insert(0, str(bybit_fetcher_path))

from app.bybit_data_fetcher.database.db_manager import DatabaseManager
from app.bybit_data_fetcher.api.bybit_client import BybitClient
from app.bybit_data_fetcher.utils.data_fetcher import DataFetcher
from app.core.symbols import get_trading_symbols

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bybit_monitor_service')

# Configuration constants (consolidated from removed config files)
CHECK_INTERVAL = 60  # Check interval in seconds
TIMEFRAME = "15"  # 15 minute timeframe
TARGET_CANDLES = 35000  # Target number of candles to fetch

# Database path configuration
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
_database_dir = os.path.join(_backend_dir, "bybit_data_fetcher", "database")
DATABASE_PATH = os.path.join(_database_dir, "bybit_market_data.db")

# Global variables for handling the monitor
is_running = True
shutdown_event = asyncio.Event()

class BybitMonitorService:
    def __init__(self):
        self.is_running = True
        self.shutdown_event = asyncio.Event()
        self.task = None
        
    async def fetch_new_candles(self, data_fetcher, symbol):
        """Fetch new candles for a symbol using the data_fetcher."""
        try:
            new_candles, error = await data_fetcher.fetch_and_store_data(symbol)
            if error:
                logger.error(f"Error fetching data for {symbol}: {error}")
                return 0
            return new_candles if new_candles else 0
        except Exception as e:
            logger.error(f"Unexpected error fetching candles for {symbol}: {str(e)}")
            return 0

    async def monitor_trading_pairs(self):
        """Continuously monitor trading pairs and fetch new candles."""
        # Ensure database directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        # Create database manager and connect
        db_manager = DatabaseManager(DATABASE_PATH)
        await db_manager.connect()
        
        trading_pairs = get_trading_symbols()
        logger.info(f"Starting Bybit monitor for {len(trading_pairs)} trading pairs")
        logger.info(f"Trading pairs: {', '.join(trading_pairs[:5])}..." if len(trading_pairs) > 5 else f"Trading pairs: {', '.join(trading_pairs)}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        
        try:
            async with BybitClient("https://api.bybit.com/v5/market/kline", "linear") as client:
                data_fetcher = DataFetcher(client, db_manager, TIMEFRAME, TARGET_CANDLES)

                while self.is_running:
                    current_time = datetime.now()
                    logger.info(f"Checking for new candles at {current_time}")

                    tasks = []
                    for symbol in trading_pairs:
                        tasks.append(self.fetch_new_candles(data_fetcher, symbol))
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result in enumerate(results):
                        symbol = trading_pairs[i]
                        if isinstance(result, Exception):
                            logger.error(f"Error processing {symbol}: {result}")
                        elif result > 0:
                            logger.info(f"Added {result} new candles for {symbol}")

                    # Reset shutdown event
                    self.shutdown_event.clear()
                    
                    # Calculate sleep time
                    next_check_time = datetime.now() + timedelta(seconds=CHECK_INTERVAL)
                    sleep_time = (next_check_time - datetime.now()).total_seconds()
                    
                    if sleep_time > 0 and self.is_running:
                        logger.debug(f"Sleeping for {sleep_time:.2f} seconds until next candle check")
                        try:
                            await asyncio.wait_for(self.shutdown_event.wait(), timeout=sleep_time)
                            if not self.is_running:
                                logger.info("Bybit monitor shutdown requested")
                                break
                        except asyncio.TimeoutError:
                            # Normal timeout - continue to next iteration
                            pass
        
        except asyncio.CancelledError:
            logger.info("Bybit monitor task was cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in Bybit monitor loop: {str(e)}", exc_info=True)
        finally:
            # Close database connection
            try:
                await db_manager.close()
                logger.info("Bybit monitor database connection closed")
            except Exception as e:
                logger.error(f"Error closing Bybit monitor database connection: {str(e)}")
            
            logger.info("Bybit monitoring stopped")

    async def start(self):
        """Start the Bybit monitor as a background task."""
        if self.task is None or self.task.done():
            self.is_running = True
            self.shutdown_event.clear()
            self.task = asyncio.create_task(self.monitor_trading_pairs())
            logger.info("Bybit monitor service started")
        else:
            logger.warning("Bybit monitor service is already running")

    async def stop(self):
        """Stop the Bybit monitor service."""
        if self.task and not self.task.done():
            self.is_running = False
            self.shutdown_event.set()
            try:
                await asyncio.wait_for(self.task, timeout=10.0)
                logger.info("Bybit monitor service stopped gracefully")
            except asyncio.TimeoutError:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                logger.warning("Bybit monitor service stopped forcefully")
        else:
            logger.info("Bybit monitor service is not running")

# Global service instance
bybit_monitor_service = BybitMonitorService() 