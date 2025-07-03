"""
TrendSpider EMA Scanner Module

This module provides functionality for scanning cryptocurrency markets for EMA (Exponential Moving Average)
conditions using data from the bybit_data_fetcher database.

Main features:
- EMA calculation and filtering
- Multiple timeframe support
- Configuration saving/loading
- REST API integration
"""

import os
import logging
from typing import Dict, Any, Optional

from . import config
from .modules import *  # Import all functions from modules
from . import symbols

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def trendspider_setup():
    """Initialize the TrendSpider module"""
    logger.info("Setting up TrendSpider EMA Scanner module")
    
    # Create necessary directories
    os.makedirs(config.CONFIG_DIR, exist_ok=True)
    os.makedirs(config.USER_CONFIG_DIR, exist_ok=True)
    
    # Create default config if it doesn't exist
    default_config_path = os.path.join(config.CONFIG_DIR, "default.json")
    if not os.path.exists(default_config_path):
        logger.info("default.json not found, creating...")
        default_config_data = config.export_current_config()
        config.save_config(default_config_data, "default", user_config=False)
    
    # Set up active config file pointer if it doesn't exist
    active_config_path = os.path.join(config.CONFIG_DIR, "active_config.json")
    if not os.path.exists(active_config_path):
        config.set_active_config("default")
    
    # Load the currently active configuration
    active_config_name = config.get_active_config_name()
    logger.info(f"Loading active configuration: {active_config_name}")
    active_cfg_data = config.load_config(active_config_name)
    if active_cfg_data:
        config.apply_config(active_cfg_data)
        logger.info(f"Applied settings from active config '{active_config_name}'")
    else:
        logger.error(f"Failed to load active config '{active_config_name}'. Using default values.")
        default_cfg = config.load_config("default", user_config=False)
        if default_cfg:
            config.apply_config(default_cfg)
    
    logger.info("TrendSpider EMA Scanner setup complete")

# Export public API
__all__ = ['trendspider_setup']
