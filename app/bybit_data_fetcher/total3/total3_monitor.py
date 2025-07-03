# THIS MUST BE THE ABSOLUTE BEGINNING OF total3/total3_monitor.py
import sys
import os

# --- Start of sys.path modification ---
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir) # This should be bybit_data_fetcher

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
    print(f"[DEBUG] Added to sys.path: {_project_root}") # Debug print
else:
    print(f"[DEBUG] Project root already in sys.path: {_project_root}") # Debug print
# --- End of sys.path modification ---

# Now, the imports should work
import asyncio
import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
from config.settings import DATABASE_PATH
from database.db_manager import DatabaseManager
from total3.total3_scraper import fetch_total3_market_cap

# Configure module-level logger
logger = logging.getLogger("total3_monitor")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def seconds_until_next_quarter(now: datetime | None = None) -> float:
    """Return the number of **seconds** until the next 15-minute boundary (UTC).

    The calculation is performed in UTC to keep it aligned with Bybit candle
    timings.  If the current time already *is* on a boundary (e.g. 14:00:00), the
    function returns 15 minutes, guaranteeing that the very first run happens at
    the *next* boundary and never immediately on start-up.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # Determine how many minutes past the hour we are and calculate remainder.
    minutes_past = now.minute % 15
    remainder_minutes = 15 - minutes_past if minutes_past != 0 else 15

    # Seconds until the next boundary (truncate current seconds).
    remainder_seconds = remainder_minutes * 60 - now.second
    if remainder_seconds <= 0:
        remainder_seconds += 15 * 60  # Fallback safeguard
    return remainder_seconds


async def monitor_total3_forever():
    """Run the TOTAL3 scraper forever at exact 15-minute UTC boundaries and persist the result."""
    db_manager = DatabaseManager(DATABASE_PATH)
    await db_manager.connect()
    try:
        while True:
            pause = seconds_until_next_quarter()
            target_time = datetime.now(timezone.utc) + timedelta(seconds=pause)
            logger.info(
                f"Sleeping for {pause:.1f}s until next quarter-hour at {target_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )
            await asyncio.sleep(pause)

            # At boundary — fetch market-cap.
            market_cap = await fetch_total3_market_cap()
            if market_cap is None:
                logger.warning("❌ TOTAL3 Market Cap could not be retrieved.")
                continue

            # Uniform logging (no suffix)
            logger.info(f"✅ TOTAL3 Market Cap: {market_cap:.2f}")

            # Build a DataFrame matching candle schema: set OHLC = market_cap, volume & turnover = 0
            boundary_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            boundary_time -= timedelta(minutes=boundary_time.minute % 15)

            df = pd.DataFrame(
                {
                    "timestamp": [boundary_time],
                    "open": [market_cap],
                    "high": [market_cap],
                    "low": [market_cap],
                    "close": [market_cap],
                    "volume": [0.0],
                    "turnover": [0.0],
                }
            )

            saved = await db_manager.save_candles("TOTAL3", df)
            if saved:
                logger.info(f"Saved TOTAL3 record at {boundary_time} -> {market_cap:.2f}")
    finally:
        await db_manager.close()
        logger.info("Database connection closed (TOTAL3 monitor)")


async def main():
    try:
        await monitor_total3_forever()
    except asyncio.CancelledError:
        logger.info("TOTAL3 monitor cancelled – shutting down.")


if __name__ == "__main__":
    asyncio.run(main()) 