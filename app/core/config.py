"""
Centralized configuration management using dotenv and environment variables.
All configuration values are loaded from .env file or environment variables.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration class that loads all settings from environment variables."""
    
    # Application Settings
    APP_NAME: str = os.getenv("APP_NAME", "Market Scanner API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    
    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Gemini AI API Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Database Configuration
    USER_DB_PATH: str = os.getenv("USER_DB_PATH", "./data/users.db")
    AI_ASSISTANT_DB_PATH: str = os.getenv("AI_ASSISTANT_DB_PATH", "./data/ai_assistant.db")
    BYBIT_DB_PATH: str = os.getenv("BYBIT_DB_PATH", "./data/bybit_market_data.db")
    
    # Cache Update Intervals (in seconds)
    FULLY_DILUTED_UPDATE_INTERVAL: int = int(os.getenv("FULLY_DILUTED_UPDATE_INTERVAL", "1800"))
    MARKET_ANALYSIS_UPDATE_INTERVAL: int = int(os.getenv("MARKET_ANALYSIS_UPDATE_INTERVAL", "2700"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Legacy compatibility properties
    @property
    def app_name(self) -> str:
        return self.APP_NAME
    
    @property
    def version(self) -> str:
        return self.VERSION
    
    @property
    def cors_origins(self) -> str:
        return self.CORS_ORIGINS
    
    @property
    def fully_diluted_update_interval(self) -> int:
        return self.FULLY_DILUTED_UPDATE_INTERVAL
    
    @property
    def market_analysis_update_interval(self) -> int:
        return self.MARKET_ANALYSIS_UPDATE_INTERVAL
    
    @property
    def gemini_api_key(self) -> Optional[str]:
        return self.GEMINI_API_KEY
    
    @property
    def database_path(self) -> str:
        return self.AI_ASSISTANT_DB_PATH

# Global configuration instance
config = Config()

# Legacy compatibility - maintain the settings object for existing code
settings = config 