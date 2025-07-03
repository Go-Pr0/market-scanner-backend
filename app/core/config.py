from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or defaults."""

    app_name: str = "Market Scanner API"
    version: str = "1.0.0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Interval in seconds for refreshing the fully-diluted cache
    fully_diluted_update_interval: int = 600  # default 10 minutes
    
    # Interval in seconds for refreshing the market analysis cache
    market_analysis_update_interval: int = 900  # default 15 minutes
    
    # Access password for API authentication
    access_password: Optional[str] = None
    
    # Logging configuration
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings() 