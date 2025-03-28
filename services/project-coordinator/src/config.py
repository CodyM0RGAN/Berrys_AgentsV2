"""
Configuration for the Project Coordinator service.

This module provides configuration settings for the service, loaded from
environment variables and configuration files.
"""
import os
from functools import lru_cache
from typing import Optional, Dict, Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings for the Project Coordinator service.
    
    Attributes:
        environment: Current environment (development, testing, production)
        debug: Debug mode flag
        service_name: Name of this service
        service_version: Version of this service
        database_url: PostgreSQL connection string
        redis_url: Redis connection string
        service_registry_url: URL of the Service Registry API
        log_level: Logging level
        artifact_storage_path: Path for storing project artifacts
    """
    
    def __hash__(self):
        """Make Settings hashable for FastAPI dependency injection."""
        return hash(self.service_name)
    
    def __eq__(self, other):
        """Implement equality check for Settings."""
        if not isinstance(other, Settings):
            return False
        return self.service_name == other.service_name
    environment: str = "development"
    debug: bool = True
    service_name: str = "project-coordinator"
    service_version: str = "0.1.0"
    database_url: str = os.environ.get("SYNC_DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/mas_framework"))
    redis_url: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    service_registry_url: Optional[str] = None
    log_level: str = "INFO"
    artifact_storage_path: str = "./artifacts"
    
    # JWT authentication settings
    auth_secret_key: str = "secret-key-for-development-only"
    auth_algorithm: str = "HS256"
    auth_token_expire_minutes: int = 30
    
    # Service integration settings
    self_registration: bool = True
    health_check_interval: int = 30  # seconds
    service_integration_url: Optional[str] = None
    
    # Project settings
    default_project_status: str = "DRAFT"
    max_artifacts_per_project: int = 1000
    
    # Resource management settings
    resource_optimization_strategy: str = "balanced"  # balanced, cost, time, quality
    
    # Feature flags
    enable_advanced_analytics: bool = True
    enable_notifications: bool = True
    
    # Model orchestration settings
    model_orchestration_url: str = os.environ.get("MODEL_ORCHESTRATION_URL", "http://model-orchestration:8000")
    model_orchestration_api_key: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "PROJECT_COORDINATOR_"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()
