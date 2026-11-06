"""
GeM BidWatch — Application Settings
Configurable via .env file or environment variables
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./gem_bidwatch.db"

    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # GeM Portal
    GEM_BASE_URL: str = "https://bidplus.gem.gov.in"
    GEM_POLL_INTERVAL_SECONDS: int = 300  # 5 minutes
    GEM_MAX_RETRIES: int = 3
    GEM_REQUEST_TIMEOUT: int = 20

    # Firebase Cloud Messaging
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    FIREBASE_PROJECT_ID: str = ""

    # Monitoring
    MONITOR_ENABLED: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
