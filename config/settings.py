"""Configuration settings for the Italian Hymns API."""

import os
import secrets
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "Italian Hymns API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Data settings
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_PATH: str = os.getenv("DATA_PATH", str(PROJECT_ROOT / "data" / "italian_hymns_full.json"))
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'hymns_history.db'}")
    
    # API settings
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # JWT Authentication settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    @classmethod
    def get_data_path(cls) -> str:
        """Get the path to the hymns data file."""
        return cls.DATA_PATH
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database URL."""
        return cls.DATABASE_URL
    
    @classmethod
    def is_debug(cls) -> bool:
        """Check if debug mode is enabled."""
        return cls.DEBUG

settings = Settings()
