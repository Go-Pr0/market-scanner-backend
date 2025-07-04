"""
TrendSpider API models
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator
from .validators import (
    timeframe_validator, ema_periods_validator, batch_size_validator,
    TIMEFRAME_validator, EMA_PERIODS_validator, BATCH_SIZE_validator
)

class ScanRequest(BaseModel):
    """Request model for EMA scan operations"""
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    ema_periods: Optional[List[int]] = None
    filter_conditions: Optional[Dict[str, str]] = None
    sort_by: Optional[str] = None
    show_only_matching: Optional[bool] = None
    batch_size: Optional[int] = None
    
    # Use shared validators
    _validate_timeframe = timeframe_validator
    _validate_ema_periods = ema_periods_validator
    _validate_batch_size = batch_size_validator

class ScanResponse(BaseModel):
    """Response model for EMA scan operations"""
    success: bool
    scan_id: Optional[str] = None
    timestamp: str
    duration_seconds: Optional[float] = None
    timeframe: Optional[str] = None
    timeframe_label: Optional[str] = None
    ema_periods: Optional[List[int]] = None
    filter_conditions: Optional[Dict[str, str]] = None
    sort_by: Optional[str] = None
    show_only_matching: Optional[bool] = None
    total_symbols_scanned: Optional[int] = None
    successful_scans: Optional[int] = None
    failed_scans: Optional[int] = None
    matching_symbols: Optional[int] = None
    results: Optional[List[Dict[str, Any]]] = None
    matching_results: Optional[List[Dict[str, Any]]] = None
    formatted_text: Optional[str] = None
    failed_symbols: Optional[List[str]] = None
    error: Optional[str] = None

class ConfigurationModel(BaseModel):
    """Model for TrendSpider configuration"""
    TIMEFRAME: str = "240"
    EMA_PERIODS: List[int] = [20, 50, 100, 200]
    FILTER_CONDITIONS: Dict[str, str] = {}
    SORT_BY: str = "symbol"
    SHOW_ONLY_MATCHING: bool = True
    FORMAT_LARGE_NUMBERS: bool = True
    CACHE_RESULTS: bool = True
    CACHE_EXPIRY: int = 300
    BATCH_SIZE: int = 4
    
    # Use shared validators
    _validate_TIMEFRAME = TIMEFRAME_validator
    _validate_EMA_PERIODS = EMA_PERIODS_validator
    _validate_BATCH_SIZE = BATCH_SIZE_validator

class ConfigurationResponse(BaseModel):
    """Response model for configuration operations"""
    success: bool
    message: Optional[str] = None
    configuration: Optional[ConfigurationModel] = None
    error: Optional[str] = None

class ConfigurationListResponse(BaseModel):
    """Response model for listing configurations"""
    success: bool
    configurations: List[str]
    error: Optional[str] = None

class SymbolListResponse(BaseModel):
    """Response model for available symbols"""
    success: bool
    symbols: List[str]
    count: int
    error: Optional[str] = None

class TimeframeOptionsResponse(BaseModel):
    """Response model for timeframe options"""
    success: bool
    timeframes: Dict[str, str]
    error: Optional[str] = None 