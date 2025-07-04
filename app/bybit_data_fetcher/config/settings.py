"""
Configuration settings for the Bybit API data fetcher.
"""
import os

# API Configuration
API_BASE_URL = "https://api.bybit.com/v5/market/kline"
API_CATEGORY = "linear"

# Data Fetch Configuration
TIMEFRAME = "15"  # 15 minute timeframe
TARGET_CANDLES = 35000  # Target number of candles to fetch

# Database Configuration
# Use absolute path to prevent issues when running from different directories
_current_dir = os.path.dirname(os.path.abspath(__file__))
_database_dir = os.path.join(os.path.dirname(_current_dir), "database")
DATABASE_PATH = os.path.join(_database_dir, "bybit_market_data.db")
