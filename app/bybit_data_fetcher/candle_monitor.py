"""
Continuous candle monitor for Bybit trading pairs.

This script continuously monitors and fetches new 15-minute candles for specified trading pairs,
maintaining an up-to-date database that can be used by different systems.
"""
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
import signal

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from config.settings import (
    API_BASE_URL, 
    API_CATEGORY, 
    TIMEFRAME,
    DATABASE_PATH,
    TARGET_CANDLES
)
from config.candle_monitor_config import (
    CHECK_INTERVAL,
    RESET_DB_ON_START,
    LOG_LEVEL,
    LOG_FILE,
    get_trading_pairs
)
from database.db_manager import DatabaseManager
from api.bybit_client import BybitClient
from utils.data_fetcher import DataFetcher

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), LOG_FILE))
    ]
)
logger = logging.getLogger('candle_monitor')

# Global variables for handling termination
is_running = True
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global is_running
    if not is_running:
        # If we've already tried to shut down once, exit forcefully
        logger.warning("Forced shutdown after multiple termination signals")
        sys.exit(0)
        
    logger.info("Received termination signal. Shutting down...")
    is_running = False
    
    # Set the event to break out of sleep
    try:
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(shutdown_event.set)
    except Exception as e:
        logger.error(f"Error in signal handler: {str(e)}")
        sys.exit(1)  # Force exit if we can't shut down gracefully

async def fetch_new_candles(data_fetcher, symbol):
    """
    Fetch new candles for a symbol using the data_fetcher.
    
    Args:
        data_fetcher: DataFetcher instance
        symbol: Trading pair symbol
        
    Returns:
        int: Number of new candles fetched and stored
    """
    new_candles, error = await data_fetcher.fetch_and_store_data(symbol)
    if error:
        logger.error(f"Error fetching data for {symbol}: {error}")
        return 0
    return new_candles if new_candles else 0

async def monitor_trading_pairs(trading_pairs, check_interval=60):
    """
    Continuously monitor trading pairs and fetch new candles.
    
    Args:
        trading_pairs: List of trading pair symbols to monitor
        check_interval: How often to check for new candles (in seconds)
    """
    global is_running
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Create database manager and connect
    db_manager = DatabaseManager(DATABASE_PATH)
    await db_manager.connect()
    
    logger.info(f"Starting continuous monitoring of {len(trading_pairs)} trading pairs")
    logger.info(f"Trading pairs: {', '.join(trading_pairs)}")
    logger.info(f"Check interval: {check_interval} seconds")
    
    last_check_time = datetime.now()
    
    try:
        async with BybitClient(API_BASE_URL, API_CATEGORY) as client:
            # Create a single DataFetcher instance to be reused
            data_fetcher = DataFetcher(client, db_manager, TIMEFRAME, TARGET_CANDLES)

            while is_running:
                current_time = datetime.now()
                logger.info(f"Checking for new candles at {current_time}")

                tasks = []
                for symbol in trading_pairs:
                    tasks.append(fetch_new_candles(data_fetcher, symbol))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    symbol = trading_pairs[i]
                    if isinstance(result, Exception):
                        logger.error(f"Error processing {symbol}: {result}", exc_info=True)
                    elif result > 0:
                        logger.info(f"Added {result} new candles for {symbol}")

                last_check_time = current_time
                
                # Reset shutdown event
                shutdown_event.clear()
                
                # Calculate sleep time
                next_check_time = datetime.now() + timedelta(seconds=check_interval)
                
                # Sleep until the next event
                sleep_time = (next_check_time - datetime.now()).total_seconds()
                
                if sleep_time > 0 and is_running:
                    logger.info(f"Sleeping for {sleep_time:.2f} seconds until next candle check")
                    try:
                        # Use wait_for with a timeout that can be interrupted by the shutdown_event
                        await asyncio.wait_for(shutdown_event.wait(), timeout=sleep_time)
                        if not is_running:
                            logger.info("Sleep interrupted for shutdown")
                            break
                    except asyncio.TimeoutError:
                        # Normal timeout - continue to next iteration
                        pass
    
    except asyncio.CancelledError:
        logger.info("Monitor task was cancelled")
    except Exception as e:
        logger.error(f"Unexpected error in monitor loop: {str(e)}", exc_info=True)
    finally:
        # Close database connection
        try:
            await db_manager.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
        
        logger.info("Monitoring stopped")
        return  # Ensure we exit the function

async def main():
    """Main entry point for the candle monitor."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Reset database if configured
    if RESET_DB_ON_START and os.path.exists(DATABASE_PATH):
        logger.warning(f"Resetting database at {DATABASE_PATH}")
        try:
            os.remove(DATABASE_PATH)
            logger.info("Database reset successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {str(e)}")
    
    # Get trading pairs from config
    trading_pairs = get_trading_pairs()
    
    if not trading_pairs:
        logger.error("No trading pairs specified in config. Exiting.")
        return
    
    # Start monitoring
    await monitor_trading_pairs(trading_pairs, CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application shutting down.")
