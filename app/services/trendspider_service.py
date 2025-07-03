"""
TrendSpider Service

This service provides EMA (Exponential Moving Average) scanning functionality
for cryptocurrency markets using data from the bybit_data_fetcher database.

Features:
- EMA calculation and filtering
- Multiple timeframe support
- Configuration management
- CSV export functionality
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from io import StringIO

from ..trendspider import config
from ..trendspider.modules import (
    get_emas_for_all_symbols,
    matches_filter_conditions,
    matches_custom_filter_conditions,
    format_results,
    sort_results,
    format_csv_for_tradingview
)
from ..trendspider import symbols

# Setup logging
logger = logging.getLogger(__name__)

class TrendSpiderService:
    """Service for managing TrendSpider EMA scanning operations"""
    
    def __init__(self):
        """Initialize the TrendSpider service"""
        self._ensure_directories()
        self._load_active_config()
    
    def _ensure_directories(self):
        """Ensure configuration directories exist"""
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        os.makedirs(config.USER_CONFIG_DIR, exist_ok=True)
        
        # Create default config if it doesn't exist
        default_config_path = os.path.join(config.CONFIG_DIR, "default.json")
        if not os.path.exists(default_config_path):
            logger.info("Creating default configuration")
            default_config_data = config.export_current_config()
            config.save_config(default_config_data, "default", user_config=False)
        
        # Set up active config file pointer if it doesn't exist
        active_config_path = os.path.join(config.CONFIG_DIR, "active_config.json")
        if not os.path.exists(active_config_path):
            config.set_active_config("default")
    
    def _load_active_config(self):
        """Load the currently active configuration"""
        active_config_name = config.get_active_config_name()
        logger.info(f"Loading active configuration: {active_config_name}")
        active_cfg_data = config.load_config(active_config_name)
        if active_cfg_data:
            config.apply_config(active_cfg_data)
            logger.info(f"Applied settings from active config '{active_config_name}'")
        else:
            logger.error(f"Failed to load active config '{active_config_name}'. Using defaults.")
            default_cfg = config.load_config("default", user_config=False)
            if default_cfg:
                config.apply_config(default_cfg)
    
    async def run_scan(self, 
                      symbols_list: Optional[List[str]] = None,
                      timeframe: Optional[str] = None,
                      ema_periods: Optional[List[int]] = None,
                      filter_conditions: Optional[Dict[str, str]] = None,
                      sort_by: Optional[str] = None,
                      show_only_matching: Optional[bool] = None,
                      batch_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run an EMA scan with the specified parameters
        
        Args:
            symbols_list: List of symbols to scan (defaults to all symbols)
            timeframe: Timeframe for the scan (defaults to current config)
            ema_periods: List of EMA periods to calculate
            filter_conditions: Dictionary of filter conditions
            sort_by: How to sort results
            show_only_matching: Whether to show only matching symbols
            batch_size: Number of symbols to process in parallel
            
        Returns:
            Dictionary containing scan results and metadata
        """
        try:
            # Use provided parameters or fall back to current config
            scan_timeframe = timeframe or config.TIMEFRAME
            scan_periods = ema_periods or config.EMA_PERIODS
            scan_symbols = symbols_list or symbols.symbols
            scan_batch_size = batch_size or config.BATCH_SIZE
            
            # Store original config values to restore later
            original_config = config.export_current_config()
            
            # Temporarily apply scan parameters
            if timeframe:
                config.TIMEFRAME = timeframe
            if ema_periods:
                config.EMA_PERIODS = ema_periods
            if filter_conditions:
                config.FILTER_CONDITIONS = filter_conditions
            if sort_by:
                config.SORT_BY = sort_by
            if show_only_matching is not None:
                config.SHOW_ONLY_MATCHING = show_only_matching
            if batch_size:
                config.BATCH_SIZE = batch_size
            
            # Run the scan
            logger.info(f"Starting EMA scan for {len(scan_symbols)} symbols")
            start_time = datetime.now()
            
            results = await get_emas_for_all_symbols(
                symbols_list=scan_symbols,
                interval=scan_timeframe,
                periods=scan_periods,
                batch_size=scan_batch_size
            )
            
            end_time = datetime.now()
            scan_duration = (end_time - start_time).total_seconds()
            
            # Count results
            total_processed = len(results)
            successful_results = [r for r in results if r.get("success", False)]
            failed_results = [r for r in results if not r.get("success", False)]
            
            # Apply filtering if specified
            if filter_conditions or config.FILTER_CONDITIONS:
                filter_to_use = filter_conditions or config.FILTER_CONDITIONS
                matching_results = []
                for result in successful_results:
                    if matches_custom_filter_conditions(result, filter_to_use):
                        matching_results.append(result)
            else:
                matching_results = successful_results
            
            # Format results for display
            formatted_text, matching_count, total_count = format_results(results)
            
            # Restore original config
            config.apply_config(original_config)
            
            return {
                "success": True,
                "scan_id": f"scan_{int(start_time.timestamp())}",
                "timestamp": start_time.isoformat(),
                "duration_seconds": scan_duration,
                "timeframe": scan_timeframe,
                "timeframe_label": config.get_timeframe_label(scan_timeframe),
                "ema_periods": scan_periods,
                "filter_conditions": filter_conditions or config.FILTER_CONDITIONS,
                "sort_by": sort_by or config.SORT_BY,
                "show_only_matching": show_only_matching if show_only_matching is not None else config.SHOW_ONLY_MATCHING,
                "total_symbols_scanned": total_processed,
                "successful_scans": len(successful_results),
                "failed_scans": len(failed_results),
                "matching_symbols": matching_count,
                "results": results,
                "matching_results": matching_results,
                "formatted_text": formatted_text,
                "failed_symbols": [r["symbol"] for r in failed_results]
            }
            
        except Exception as e:
            logger.error(f"Error running EMA scan: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_scan_results_csv(self, scan_results: Dict[str, Any]) -> Tuple[str, str]:
        """
        Convert scan results to CSV format
        
        Args:
            scan_results: Results from run_scan method
            
        Returns:
            Tuple of (CSV content, filename)
        """
        try:
            if not scan_results.get("success", False):
                raise ValueError("Invalid scan results")
            
            results = scan_results.get("results", [])
            csv_content, matching_count, total_count = format_csv_for_tradingview(results)
            
            # Generate filename
            timestamp = scan_results.get("timestamp", datetime.now().isoformat())
            timeframe = scan_results.get("timeframe_label", "unknown")
            filename = f"ema_scan_{timeframe}_{timestamp[:19].replace(':', '-')}.csv"
            
            return csv_content, filename
            
        except Exception as e:
            logger.error(f"Error generating CSV: {str(e)}")
            raise
    
    def list_configurations(self, user_configs: bool = True) -> List[str]:
        """
        List available configurations
        
        Args:
            user_configs: Whether to list user configs (True) or system configs (False)
            
        Returns:
            List of configuration names
        """
        return config.list_configs(user_configs)
    
    def get_configuration(self, config_name: str, user_config: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a specific configuration
        
        Args:
            config_name: Name of the configuration
            user_config: Whether to look in user configs (True) or system configs (False)
            
        Returns:
            Configuration dictionary or None if not found
        """
        return config.load_config(config_name, user_config)
    
    def save_configuration(self, config_data: Dict[str, Any], config_name: str, user_config: bool = True) -> bool:
        """
        Save a configuration
        
        Args:
            config_data: Configuration data to save
            config_name: Name for the configuration
            user_config: Whether to save as user config (True) or system config (False)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config.save_config(config_data, config_name, user_config)
            return True
        except Exception as e:
            logger.error(f"Error saving configuration '{config_name}': {str(e)}")
            return False
    
    def delete_configuration(self, config_name: str, user_config: bool = True) -> bool:
        """
        Delete a configuration
        
        Args:
            config_name: Name of the configuration to delete
            user_config: Whether to delete from user configs (True) or system configs (False)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return config.delete_config(config_name, user_config)
    
    def get_active_configuration(self) -> str:
        """
        Get the name of the currently active configuration
        
        Returns:
            Active configuration name
        """
        return config.get_active_config_name()
    
    def set_active_configuration(self, config_name: str) -> bool:
        """
        Set the active configuration
        
        Args:
            config_name: Name of the configuration to make active
            
        Returns:
            True if set successfully, False otherwise
        """
        success = config.set_active_config(config_name)
        if success:
            self._load_active_config()
        return success
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get the current configuration settings
        
        Returns:
            Current configuration dictionary
        """
        return config.export_current_config()
    
    def apply_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Apply configuration settings temporarily (without saving)
        
        Args:
            config_data: Configuration data to apply
            
        Returns:
            True if applied successfully, False otherwise
        """
        try:
            config.apply_config(config_data)
            return True
        except Exception as e:
            logger.error(f"Error applying configuration: {str(e)}")
            return False
    
    def get_available_symbols(self) -> List[str]:
        """
        Get the list of available symbols for scanning
        
        Returns:
            List of symbol names
        """
        return symbols.symbols.copy()
    
    def get_timeframe_options(self) -> Dict[str, str]:
        """
        Get available timeframe options
        
        Returns:
            Dictionary mapping timeframe codes to human-readable labels
        """
        return {
            "1": "1 minute",
            "5": "5 minutes", 
            "15": "15 minutes",
            "30": "30 minutes",
            "60": "1 hour",
            "120": "2 hours",
            "240": "4 hours",
            "360": "6 hours",
            "720": "12 hours",
            "1440": "1 day"
        }
    
    def validate_configuration(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a configuration
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["TIMEFRAME", "EMA_PERIODS", "FILTER_CONDITIONS", "SORT_BY"]
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate timeframe
        if "TIMEFRAME" in config_data:
            valid_timeframes = ["1", "5", "15", "30", "60", "120", "240", "360", "720", "1440"]
            if config_data["TIMEFRAME"] not in valid_timeframes:
                errors.append(f"Invalid timeframe: {config_data['TIMEFRAME']}")
        
        # Validate EMA periods
        if "EMA_PERIODS" in config_data:
            if not isinstance(config_data["EMA_PERIODS"], list):
                errors.append("EMA_PERIODS must be a list")
            elif not all(isinstance(p, int) and p > 0 for p in config_data["EMA_PERIODS"]):
                errors.append("EMA_PERIODS must contain positive integers")
            elif len(config_data["EMA_PERIODS"]) > 5:
                errors.append("EMA_PERIODS cannot contain more than 5 periods")
        
        # Validate filter conditions
        if "FILTER_CONDITIONS" in config_data:
            if not isinstance(config_data["FILTER_CONDITIONS"], dict):
                errors.append("FILTER_CONDITIONS must be a dictionary")
            else:
                valid_conditions = ["above", "below", "cross_above", "cross_below"]
                for period_str, condition in config_data["FILTER_CONDITIONS"].items():
                    # Check if period is valid
                    try:
                        period = int(period_str)
                        if period <= 0:
                            errors.append(f"Invalid EMA period in filter conditions: {period_str}")
                    except ValueError:
                        errors.append(f"Invalid EMA period in filter conditions: {period_str}")
                    
                    # Check if condition is valid
                    if not (condition in valid_conditions or 
                           condition.startswith("above_by:") or 
                           condition.startswith("below_by:") or 
                           condition.startswith("near:")):
                        errors.append(f"Invalid filter condition: {condition}")
        
        # Validate sort_by
        if "SORT_BY" in config_data:
            valid_sorts = ["symbol", "price", "volume"]
            sort_by = config_data["SORT_BY"]
            if not (sort_by in valid_sorts or sort_by.startswith("percent_")):
                errors.append(f"Invalid sort_by value: {sort_by}")
        
        # Validate boolean fields
        boolean_fields = ["SHOW_ONLY_MATCHING", "FORMAT_LARGE_NUMBERS", "CACHE_RESULTS"]
        for field in boolean_fields:
            if field in config_data and not isinstance(config_data[field], bool):
                errors.append(f"{field} must be a boolean")
        
        # Validate numeric fields
        if "BATCH_SIZE" in config_data:
            if not isinstance(config_data["BATCH_SIZE"], int) or config_data["BATCH_SIZE"] < 1 or config_data["BATCH_SIZE"] > 10:
                errors.append("BATCH_SIZE must be an integer between 1 and 10")
        
        if "CACHE_EXPIRY" in config_data:
            if not isinstance(config_data["CACHE_EXPIRY"], int) or config_data["CACHE_EXPIRY"] < 0:
                errors.append("CACHE_EXPIRY must be a non-negative integer")
        
        return len(errors) == 0, errors

# Create a singleton instance
trendspider_service = TrendSpiderService() 