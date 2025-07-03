"""
TrendSpider API Models

Pydantic models for TrendSpider EMA scanner API endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class ScanRequest(BaseModel):
    """Request model for running an EMA scan"""
    symbols: Optional[List[str]] = Field(None, description="List of symbols to scan (defaults to all symbols)")
    timeframe: Optional[str] = Field(None, description="Timeframe for the scan (e.g., '240' for 4h)")
    ema_periods: Optional[List[int]] = Field(None, description="List of EMA periods to calculate")
    filter_conditions: Optional[Dict[str, str]] = Field(None, description="Dictionary of filter conditions")
    sort_by: Optional[str] = Field(None, description="How to sort results")
    show_only_matching: Optional[bool] = Field(None, description="Whether to show only matching symbols")
    batch_size: Optional[int] = Field(None, description="Number of symbols to process in parallel")
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        if v is not None:
            valid_timeframes = ["1", "5", "15", "30", "60", "120", "240", "360", "720", "1440"]
            if v not in valid_timeframes:
                raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
        return v
    
    @validator('ema_periods')
    def validate_ema_periods(cls, v):
        if v is not None:
            if not all(isinstance(p, int) and p > 0 for p in v):
                raise ValueError("EMA periods must be positive integers")
            if len(v) > 5:
                raise ValueError("Cannot specify more than 5 EMA periods")
        return v
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError("Batch size must be between 1 and 10")
        return v

class SymbolResult(BaseModel):
    """Result for a single symbol"""
    symbol: str
    success: bool
    price: Optional[float] = None
    volume: Optional[float] = None
    emas: Optional[Dict[str, float]] = None
    percent_from_ema: Optional[Dict[str, float]] = None
    timestamp: str
    timeframe: Optional[str] = None
    actual_timeframe_minutes: Optional[int] = None
    candles_available: Optional[int] = None
    error: Optional[str] = None

class ScanResponse(BaseModel):
    """Response model for EMA scan results"""
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
    results: Optional[List[SymbolResult]] = None
    matching_results: Optional[List[SymbolResult]] = None
    formatted_text: Optional[str] = None
    failed_symbols: Optional[List[str]] = None
    error: Optional[str] = None

class ConfigurationModel(BaseModel):
    """Model for TrendSpider configuration"""
    TIMEFRAME: str = Field(..., description="Timeframe for EMA calculations")
    EMA_PERIODS: List[int] = Field(..., description="List of EMA periods to calculate")
    FILTER_CONDITIONS: Dict[str, str] = Field(..., description="Dictionary of filter conditions")
    SORT_BY: str = Field(..., description="How to sort results")
    SHOW_ONLY_MATCHING: bool = Field(True, description="Whether to show only matching symbols")
    FORMAT_LARGE_NUMBERS: bool = Field(True, description="Whether to format large numbers")
    BATCH_SIZE: int = Field(4, description="Number of symbols to process in parallel")
    CACHE_RESULTS: bool = Field(False, description="Whether to cache results")
    CACHE_EXPIRY: int = Field(300, description="Cache expiry time in seconds")
    
    @validator('TIMEFRAME')
    def validate_timeframe(cls, v):
        valid_timeframes = ["1", "5", "15", "30", "60", "120", "240", "360", "720", "1440"]
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
        return v
    
    @validator('EMA_PERIODS')
    def validate_ema_periods(cls, v):
        if not all(isinstance(p, int) and p > 0 for p in v):
            raise ValueError("EMA periods must be positive integers")
        if len(v) > 5:
            raise ValueError("Cannot specify more than 5 EMA periods")
        return v
    
    @validator('BATCH_SIZE')
    def validate_batch_size(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Batch size must be between 1 and 10")
        return v
    
    @validator('CACHE_EXPIRY')
    def validate_cache_expiry(cls, v):
        if v < 0:
            raise ValueError("Cache expiry must be non-negative")
        return v

class ConfigurationCreateRequest(BaseModel):
    """Request model for creating a new configuration"""
    name: str = Field(..., description="Name for the configuration")
    config: ConfigurationModel = Field(..., description="Configuration data")
    user_config: bool = Field(True, description="Whether to save as user config")

class ConfigurationUpdateRequest(BaseModel):
    """Request model for updating a configuration"""
    config: ConfigurationModel = Field(..., description="Updated configuration data")
    user_config: bool = Field(True, description="Whether to update user config")

class ConfigurationResponse(BaseModel):
    """Response model for configuration operations"""
    success: bool
    message: Optional[str] = None
    config: Optional[ConfigurationModel] = None
    error: Optional[str] = None

class ConfigurationListResponse(BaseModel):
    """Response model for listing configurations"""
    success: bool
    configurations: List[str]
    active_config: str
    error: Optional[str] = None

class ValidationResponse(BaseModel):
    """Response model for configuration validation"""
    is_valid: bool
    errors: List[str]

class TimeframeOptionsResponse(BaseModel):
    """Response model for timeframe options"""
    timeframes: Dict[str, str]

class SymbolsResponse(BaseModel):
    """Response model for available symbols"""
    symbols: List[str]
    count: int

class ActiveConfigResponse(BaseModel):
    """Response model for active configuration"""
    active_config: str
    config_data: ConfigurationModel

class SetActiveConfigRequest(BaseModel):
    """Request model for setting active configuration"""
    config_name: str = Field(..., description="Name of the configuration to make active")

class BasicResponse(BaseModel):
    """Basic response model"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None 