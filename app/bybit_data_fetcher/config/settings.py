"""
Configuration settings for bybit_data_fetcher module.
This module imports from the centralized config to maintain consistency.
"""

import sys
import os

# Add the parent directories to sys.path to import from app.core.config
current_dir = os.path.dirname(os.path.abspath(__file__))
bybit_fetcher_dir = os.path.dirname(current_dir)
app_dir = os.path.dirname(bybit_fetcher_dir)
backend_dir = os.path.dirname(app_dir)

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.core.config import config
    DATABASE_PATH = config.BYBIT_DB_PATH
except ImportError:
    # Fallback if import fails
    DATABASE_PATH = "./data/bybit_market_data.db"