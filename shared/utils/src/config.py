"""
Configuration management utilities for the Berrys_AgentsV2 project.

This module provides utilities for loading and managing configuration settings
across services, including:
- Environment variable handling
- Configuration file loading
- Hierarchical configuration with defaults
"""

import json
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel, Field, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar('T', bound=BaseSettings)


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class LogLevel(str, Enum):
    """Log level."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BaseServiceConfig(BaseSettings):
    """Base configuration for all services."""
    
    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    # Service
    service_name: str = Field(
        ...,
        description="Service name"
    )
    service_version: str = Field(
        default="0.1.0",
        description="Service version"
    )
    
    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://sa:Passw0rd@localhost:5432/mas_framework",
        description="Database URL"
    )
    
    # Logging
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Log level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL"
    )
    
    # API
    api_prefix: str = Field(
        default="/api",
        description="API prefix"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    # Security
    secret_key: str = Field(
        default="insecure-secret-key-for-development-only",
        description="Secret key for security"
    )
    token_expiration: int = Field(
        default=3600,
        description="Token expiration in seconds"
    )
    
    # Timeouts
    default_timeout: int = Field(
        default=30,
        description="Default timeout in seconds"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    def get_database_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy database connection arguments.

        Returns:
            A dictionary of database connection arguments.
        """
        return {
            "url": self.database_url,
            "connect_args": {
                "connect_timeout": self.default_timeout
            }
        }
    
    def get_redis_args(self) -> Dict[str, Any]:
        """
        Get Redis connection arguments.

        Returns:
            A dictionary of Redis connection arguments.
        """
        return {
            "url": self.redis_url,
            "socket_timeout": self.default_timeout,
            "socket_connect_timeout": self.default_timeout
        }
    
    def is_development(self) -> bool:
        """
        Check if the environment is development.

        Returns:
            True if the environment is development, False otherwise.
        """
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """
        Check if the environment is testing.

        Returns:
            True if the environment is testing, False otherwise.
        """
        return self.environment == Environment.TESTING
    
    def is_staging(self) -> bool:
        """
        Check if the environment is staging.

        Returns:
            True if the environment is staging, False otherwise.
        """
        return self.environment == Environment.STAGING
    
    def is_production(self) -> bool:
        """
        Check if the environment is production.

        Returns:
            True if the environment is production, False otherwise.
        """
        return self.environment == Environment.PRODUCTION


def load_config(config_class: Type[T], env_prefix: Optional[str] = None) -> T:
    """
    Load configuration from environment variables and .env file.

    Args:
        config_class: The configuration class to load.
        env_prefix: Optional prefix for environment variables.

    Returns:
        An instance of the configuration class.
    """
    # Create settings with environment variables
    settings_dict = {}
    
    if env_prefix:
        # Use the provided prefix
        settings_dict["env_prefix"] = env_prefix
    else:
        # Generate a prefix from the class name
        class_name = config_class.__name__
        if class_name.endswith("Config"):
            class_name = class_name[:-6]
        
        # Convert CamelCase to SCREAMING_SNAKE_CASE
        env_prefix = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).upper()
        settings_dict["env_prefix"] = f"{env_prefix}_"
    
    # Check if environment is set and convert to uppercase
    env_var_name = f"{env_prefix}_ENVIRONMENT" if env_prefix else "ENVIRONMENT"
    environment = os.environ.get(env_var_name)
    if environment:
        os.environ[env_var_name] = environment.upper()
    
    # Load configuration
    return config_class(**settings_dict)


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries.

    Later dictionaries take precedence over earlier ones.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        A merged configuration dictionary.
    """
    result = {}
    
    for config in configs:
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = merge_configs(result[key], value)
            else:
                # Override or add the value
                result[key] = value
    
    return result


def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        A dictionary with the configuration.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(file_path, "r") as f:
        return json.load(f)


def create_config_model(
    name: str,
    **field_definitions: Any
) -> Type[BaseSettings]:
    """
    Create a configuration model with the specified fields.

    Args:
        name: The name of the model.
        **field_definitions: Field definitions as keyword arguments.

    Returns:
        A new configuration model class.
    """
    return create_model(
        name,
        __base__=BaseServiceConfig,
        **field_definitions
    )


def get_env_var(
    name: str,
    default: Optional[Any] = None,
    required: bool = False
) -> Any:
    """
    Get an environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value if the environment variable is not set.
        required: Whether the environment variable is required.

    Returns:
        The value of the environment variable, or the default value if not set.

    Raises:
        ValueError: If the environment variable is required but not set.
    """
    value = os.environ.get(name)
    
    if value is None:
        if required:
            raise ValueError(f"Required environment variable {name} is not set")
        return default
    
    return value


def get_env_bool(
    name: str,
    default: Optional[bool] = None,
    required: bool = False
) -> bool:
    """
    Get a boolean environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value if the environment variable is not set.
        required: Whether the environment variable is required.

    Returns:
        The boolean value of the environment variable, or the default value if not set.

    Raises:
        ValueError: If the environment variable is required but not set, or if the value is not a valid boolean.
    """
    value = get_env_var(name, None, required)
    
    if value is None:
        if default is None:
            return False
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value = value.lower()
        if value in ("true", "1", "yes", "y", "on"):
            return True
        if value in ("false", "0", "no", "n", "off"):
            return False
    
    raise ValueError(f"Invalid boolean value for environment variable {name}: {value}")


def get_env_int(
    name: str,
    default: Optional[int] = None,
    required: bool = False
) -> int:
    """
    Get an integer environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value if the environment variable is not set.
        required: Whether the environment variable is required.

    Returns:
        The integer value of the environment variable, or the default value if not set.

    Raises:
        ValueError: If the environment variable is required but not set, or if the value is not a valid integer.
    """
    value = get_env_var(name, None, required)
    
    if value is None:
        if default is None:
            return 0
        return default
    
    if isinstance(value, int):
        return value
    
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid integer value for environment variable {name}: {value}")


def get_env_float(
    name: str,
    default: Optional[float] = None,
    required: bool = False
) -> float:
    """
    Get a float environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value if the environment variable is not set.
        required: Whether the environment variable is required.

    Returns:
        The float value of the environment variable, or the default value if not set.

    Raises:
        ValueError: If the environment variable is required but not set, or if the value is not a valid float.
    """
    value = get_env_var(name, None, required)
    
    if value is None:
        if default is None:
            return 0.0
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid float value for environment variable {name}: {value}")


def get_env_list(
    name: str,
    default: Optional[List[str]] = None,
    required: bool = False,
    separator: str = ","
) -> List[str]:
    """
    Get a list environment variable.

    Args:
        name: The name of the environment variable.
        default: The default value if the environment variable is not set.
        required: Whether the environment variable is required.
        separator: The separator to split the list.

    Returns:
        The list value of the environment variable, or the default value if not set.

    Raises:
        ValueError: If the environment variable is required but not set.
    """
    value = get_env_var(name, None, required)
    
    if value is None:
        if default is None:
            return []
        return default
    
    if isinstance(value, list):
        return value
    
    if isinstance(value, str):
        if not value:
            return []
        return [item.strip() for item in value.split(separator)]
    
    raise ValueError(f"Invalid list value for environment variable {name}: {value}")


def get_settings(settings_class=None):
    """
    Get settings instance.
    
    Args:
        settings_class: Optional settings class to use. If not provided,
                       BaseServiceConfig will be used.
    
    Returns:
        An instance of the settings class.
    """
    if settings_class is None:
        return load_config(BaseServiceConfig)
    return load_config(settings_class)
