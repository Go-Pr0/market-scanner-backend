import os
import json
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default configuration values
TIMEFRAME = "240"  # 4H timeframe
EMA_PERIODS = [200]
FILTER_CONDITIONS = {200: "above"}
SORT_BY = "symbol"
SHOW_ONLY_MATCHING = True
FORMAT_LARGE_NUMBERS = True
BATCH_SIZE = 4
CACHE_RESULTS = False
CACHE_EXPIRY = 300  # 5 minutes

# Configuration directories
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
USER_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "my_configs")

# Ensure config directories exist
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)
if not os.path.exists(USER_CONFIG_DIR):
    os.makedirs(USER_CONFIG_DIR)

def get_active_config_name() -> str:
    """Get the name of the active configuration"""
    active_config_path = os.path.join(CONFIG_DIR, "active_config.json")
    try:
        with open(active_config_path, 'r') as f:
            active_config = json.load(f)
            return active_config.get("active_config", "default")
    except Exception:
        return "default"

def load_config(config_name: Optional[str] = None, user_config: bool = True) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_dir = USER_CONFIG_DIR if user_config else CONFIG_DIR

    if config_name is None:
        active_config_path = os.path.join(CONFIG_DIR, "active_config.json")
        try:
            with open(active_config_path, 'r') as f:
                active_config = json.load(f)
                config_name = active_config.get("active_config", "default")
        except Exception as e:
            logger.error(f"Error loading active config: {str(e)}")
            config_name = "default"

    config_path = os.path.join(config_dir, f"{config_name}.json")
    if not os.path.exists(config_path) and user_config:
        config_path = os.path.join(CONFIG_DIR, f"{config_name}.json")

    if not os.path.exists(config_path):
        logger.info(f"Config file {config_path} not found, using default.json")
        config_path = os.path.join(CONFIG_DIR, "default.json")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            # Remove schedule keys if they exist in old files
            config.pop("scheduled_scan_enabled", None)
            config.pop("scheduled_scan_hour", None)
            config.pop("scheduled_scan_minute", None)
            config.pop("scheduled_scan_config", None)
            config.pop("auto_scan_interval", None) # Also remove auto scan if present
            return config
    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {str(e)}")
        return {}

def save_config(config: Dict[str, Any], config_name: str, user_config: bool = True) -> None:
    """Save configuration to JSON file"""
    config_dir = USER_CONFIG_DIR if user_config else CONFIG_DIR

    # Sanitize config_name to be safe for filesystem
    config_name = config_name.replace('/', '_').replace('\\', '_')

    # Ensure schedule keys are not saved
    config_to_save = config.copy()
    config_to_save.pop("scheduled_scan_enabled", None)
    config_to_save.pop("scheduled_scan_hour", None)
    config_to_save.pop("scheduled_scan_minute", None)
    config_to_save.pop("scheduled_scan_config", None)
    config_to_save.pop("auto_scan_interval", None)

    try:
        config_path = os.path.join(config_dir, f"{config_name}.json")
        with open(config_path, 'w') as f:
            json.dump(config_to_save, f, indent=4)
            logger.info(f"Saved configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config file {config_path}: {str(e)}")

def delete_config(config_name: str, user_config: bool = True) -> bool:
    """Delete a configuration file"""
    config_dir = USER_CONFIG_DIR if user_config else CONFIG_DIR
    config_path = os.path.join(config_dir, f"{config_name}.json")

    try:
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f"Deleted configuration file {config_path}")
            return True
        else:
            logger.warning(f"Config file {config_path} not found, cannot delete")
            return False
    except Exception as e:
        logger.error(f"Error deleting config file {config_path}: {str(e)}")
        return False

def list_configs(user_config: bool = True) -> List[str]:
    """List all available configurations"""
    config_dir = USER_CONFIG_DIR if user_config else CONFIG_DIR
    
    try:
        # List user configs first
        if user_config:
            files = [f[:-5] for f in os.listdir(config_dir) if f.endswith('.json')]
            logger.info(f"Found {len(files)} user configs in {config_dir}")
            
        # List system configs
        else:
            files = [f[:-5] for f in os.listdir(config_dir) if f.endswith('.json') and f != 'active_config.json']
            logger.info(f"Found {len(files)} system configs in {config_dir}")
            
        return sorted(files)
    except Exception as e:
        logger.error(f"Error listing configs in {config_dir}: {str(e)}")
        return []

def set_active_config(config_name: str) -> bool:
    """Set the active configuration"""
    active_config_path = os.path.join(CONFIG_DIR, "active_config.json")
    try:
        with open(active_config_path, 'w') as f:
            json.dump({"active_config": config_name}, f, indent=4)
            logger.info(f"Set active configuration to {config_name}")
            return True
    except Exception as e:
        logger.error(f"Error setting active config to {config_name}: {str(e)}")
        return False

def apply_config(config: Dict[str, Any]) -> None:
    """Apply configuration values from config dict to global variables"""
    global TIMEFRAME, EMA_PERIODS, FILTER_CONDITIONS, SORT_BY
    global SHOW_ONLY_MATCHING, FORMAT_LARGE_NUMBERS, BATCH_SIZE
    global CACHE_RESULTS, CACHE_EXPIRY
    
    try:
        if "TIMEFRAME" in config:
            TIMEFRAME = config["TIMEFRAME"]
            logger.info(f"Applied TIMEFRAME: {TIMEFRAME}")
            
        if "EMA_PERIODS" in config:
            EMA_PERIODS = config["EMA_PERIODS"]
            logger.info(f"Applied EMA_PERIODS: {EMA_PERIODS}")
            
        if "FILTER_CONDITIONS" in config:
            FILTER_CONDITIONS = config["FILTER_CONDITIONS"]
            logger.info(f"Applied FILTER_CONDITIONS: {FILTER_CONDITIONS}")
            
        if "SORT_BY" in config:
            SORT_BY = config["SORT_BY"]
            logger.info(f"Applied SORT_BY: {SORT_BY}")
            
        if "SHOW_ONLY_MATCHING" in config:
            SHOW_ONLY_MATCHING = config["SHOW_ONLY_MATCHING"]
            logger.info(f"Applied SHOW_ONLY_MATCHING: {SHOW_ONLY_MATCHING}")
            
        if "FORMAT_LARGE_NUMBERS" in config:
            FORMAT_LARGE_NUMBERS = config["FORMAT_LARGE_NUMBERS"]
            logger.info(f"Applied FORMAT_LARGE_NUMBERS: {FORMAT_LARGE_NUMBERS}")
            
        if "BATCH_SIZE" in config:
            BATCH_SIZE = config["BATCH_SIZE"]
            logger.info(f"Applied BATCH_SIZE: {BATCH_SIZE}")
            
        if "CACHE_RESULTS" in config:
            CACHE_RESULTS = config["CACHE_RESULTS"]
            logger.info(f"Applied CACHE_RESULTS: {CACHE_RESULTS}")
            
        if "CACHE_EXPIRY" in config:
            CACHE_EXPIRY = config["CACHE_EXPIRY"]
            logger.info(f"Applied CACHE_EXPIRY: {CACHE_EXPIRY}")
    except Exception as e:
        logger.error(f"Error applying configuration: {str(e)}")

def export_current_config() -> Dict[str, Any]:
    """Export the current configuration as a dictionary"""
    config = {
        "TIMEFRAME": TIMEFRAME,
        "EMA_PERIODS": EMA_PERIODS,
        "FILTER_CONDITIONS": FILTER_CONDITIONS,
        "SORT_BY": SORT_BY,
        "SHOW_ONLY_MATCHING": SHOW_ONLY_MATCHING,
        "FORMAT_LARGE_NUMBERS": FORMAT_LARGE_NUMBERS,
        "BATCH_SIZE": BATCH_SIZE,
        "CACHE_RESULTS": CACHE_RESULTS,
        "CACHE_EXPIRY": CACHE_EXPIRY
    }
    return config

def get_timeframe_label(timeframe: str) -> str:
    """Get human-readable timeframe label"""
    mapping = {"1": "1m", "5": "5m", "15": "15m", "30": "30m", "60": "1h", 
               "120": "2h", "240": "4h", "360": "6h", "720": "12h", "1440": "1d"}
    return mapping.get(timeframe, f"{timeframe}m")

# AI configuration generation has been removed to eliminate external dependencies
