"""
Configuration for the Agent Orchestrator service.

This module provides configuration settings for the Agent Orchestrator service.
"""

import os
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """
    Environment enum.
    """
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class AgentOrchestratorConfig(BaseSettings):
    """
    Configuration settings for the Agent Orchestrator service.
    """
    # Service settings
    service_name: str = "agent-orchestrator"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: str = "INFO"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings
    database_url: Optional[str] = None
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "mas_framework"
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_schema: str = "agent_orchestrator"
    
    # JWT settings
    jwt_secret: str = "secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    
    # Messaging settings
    rabbitmq_url: Optional[str] = None
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    
    # Redis settings
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Agent settings
    max_agents_per_project: int = 10
    default_agent_timeout: int = 300  # 5 minutes
    
    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    
    @field_validator('environment')
    def validate_environment(cls, v):
        """
        Validate environment.
        """
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                raise ValueError(f"Invalid environment: {v}")
        return v
    
    @model_validator(mode='after')
    def set_database_url(self):
        """
        Set database URL if not provided.
        """
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
                f"@{self.database_host}:{self.database_port}/{self.database_name}"
            )
        return self
    
    @model_validator(mode='after')
    def set_rabbitmq_url(self):
        """
        Set RabbitMQ URL if not provided.
        """
        if not self.rabbitmq_url:
            self.rabbitmq_url = (
                f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
                f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
            )
        return self
    
    @model_validator(mode='after')
    def set_redis_url(self):
        """
        Set Redis URL if not provided.
        """
        if not self.redis_url:
            if self.redis_password:
                self.redis_url = (
                    f"redis://:{self.redis_password}"
                    f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
                )
            else:
                self.redis_url = (
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
                )
        return self
    
    def is_development(self) -> bool:
        """
        Check if environment is development.
        
        Returns:
            bool: True if environment is development, False otherwise
        """
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """
        Check if environment is testing.
        
        Returns:
            bool: True if environment is testing, False otherwise
        """
        return self.environment == Environment.TESTING
    
    def is_staging(self) -> bool:
        """
        Check if environment is staging.
        
        Returns:
            bool: True if environment is staging, False otherwise
        """
        return self.environment == Environment.STAGING
    
    def is_production(self) -> bool:
        """
        Check if environment is production.
        
        Returns:
            bool: True if environment is production, False otherwise
        """
        return self.environment == Environment.PRODUCTION
    
    def get_feature_flag(self, name: str, default: bool = False) -> bool:
        """
        Get feature flag value.
        
        Args:
            name: Feature flag name
            default: Default value if feature flag not found
            
        Returns:
            bool: Feature flag value
        """
        return self.feature_flags.get(name, default)
    
    class Config:
        env_prefix = "AGENT_ORCHESTRATOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create config instance
config = AgentOrchestratorConfig()

def get_settings() -> AgentOrchestratorConfig:
    """
    Get the application settings.
    
    Returns:
        AgentOrchestratorConfig: Application settings
    """
    return config
