"""
Shared Pydantic validators for TrendSpider models
"""
from typing import List, Dict, Any
from pydantic import validator


def validate_timeframe(cls, v):
    """Validate timeframe value"""
    if v is None:
        return v
    valid_timeframes = ["1", "5", "15", "30", "60", "120", "240", "360", "720", "1440"]
    if v not in valid_timeframes:
        raise ValueError(f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}")
    return v


def validate_ema_periods(cls, v):
    """Validate EMA periods list"""
    if v is None:
        return v
    if not isinstance(v, list):
        raise ValueError("EMA periods must be a list")
    if len(v) == 0:
        raise ValueError("EMA periods list cannot be empty")
    if len(v) > 5:
        raise ValueError("Cannot specify more than 5 EMA periods")
    for period in v:
        if not isinstance(period, int) or period <= 0:
            raise ValueError("EMA periods must be positive integers")
    return v


def validate_batch_size(cls, v):
    """Validate batch size value"""
    if v is None:
        return v
    if not isinstance(v, int) or v < 1 or v > 10:
        raise ValueError("Batch size must be an integer between 1 and 10")
    return v


# Validator decorators that can be reused
timeframe_validator = validator('timeframe', allow_reuse=True)(validate_timeframe)
ema_periods_validator = validator('ema_periods', allow_reuse=True)(validate_ema_periods)
batch_size_validator = validator('batch_size', allow_reuse=True)(validate_batch_size)

# Uppercase field validators for ConfigurationModel
# These reuse the same validation functions but target uppercase field names
TIMEFRAME_validator = validator('TIMEFRAME', allow_reuse=True)(validate_timeframe)
EMA_PERIODS_validator = validator('EMA_PERIODS', allow_reuse=True)(validate_ema_periods)
BATCH_SIZE_validator = validator('BATCH_SIZE', allow_reuse=True)(validate_batch_size) 