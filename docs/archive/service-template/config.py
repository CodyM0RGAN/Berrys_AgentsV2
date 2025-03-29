import os
from functools import lru_cache
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any, List


class Settings(BaseSettings):
    """
    Service configuration settings.
    Loaded from environment variables and/or .env file.
    """
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    service_name: str = Field("service-name", env="SERVICE_NAME")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(30, env="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(1800, env="DB_POOL_RECYCLE")
    
    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Authentication
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Service-specific settings
    request_timeout: float = Field(30.0, env="REQUEST_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # External services
    external_service_url: Optional[str] = Field(None, env="EXTERNAL_SERVICE_URL")
    
    # Feature flags
    enable_feature_x: bool = Field(False, env="ENABLE_FEATURE_X")
    enable_feature_y: bool = Field(False, env="ENABLE_FEATURE_Y")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(None, env="SENTRY_DSN")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Service configuration settings
    """
    return Settings()
