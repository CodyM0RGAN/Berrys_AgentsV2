"""
Configuration management for tests.

This module provides utilities for managing test configurations for different environments.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Type, TypeVar, Generic, Union, List
from pydantic import BaseModel, Field

T = TypeVar('T', bound=BaseModel)


class TestEnvironment(str):
    """Test environment enum."""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class BaseTestConfig(BaseModel):
    """
    Base test configuration.
    
    This class provides a base for test configurations.
    """
    
    environment: str = Field(default=TestEnvironment.LOCAL, description="Test environment")
    
    # Database configuration
    database_url: Optional[str] = Field(None, description="Database URL")
    database_echo: bool = Field(False, description="Whether to echo SQL statements")
    
    # API configuration
    api_base_url: str = Field("http://test", description="API base URL")
    api_timeout: float = Field(10.0, description="API request timeout in seconds")
    
    # Authentication configuration
    auth_enabled: bool = Field(False, description="Whether authentication is enabled")
    auth_token_url: str = Field("/token", description="Authentication token URL")
    
    # Logging configuration
    log_level: str = Field("INFO", description="Log level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Test data configuration
    test_data_dir: str = Field("test_data", description="Test data directory")
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"


class ConfigLoader:
    """
    Configuration loader.
    
    This class provides utilities for loading test configurations from various sources.
    """
    
    @staticmethod
    def from_env(config_class: Type[T], prefix: str = "TEST_") -> T:
        """
        Load configuration from environment variables.
        
        Args:
            config_class: Configuration class
            prefix: Environment variable prefix
            
        Returns:
            T: Configuration instance
        """
        # Get all environment variables with the prefix
        env_vars = {
            k[len(prefix):].lower(): v
            for k, v in os.environ.items()
            if k.startswith(prefix)
        }
        
        # Convert values to appropriate types
        for key, value in env_vars.items():
            # Convert boolean strings
            if value.lower() in ("true", "yes", "1"):
                env_vars[key] = True
            elif value.lower() in ("false", "no", "0"):
                env_vars[key] = False
            
            # Convert numeric strings
            elif value.isdigit():
                env_vars[key] = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                env_vars[key] = float(value)
        
        # Create configuration instance
        return config_class(**env_vars)
    
    @staticmethod
    def from_json(config_class: Type[T], file_path: str) -> T:
        """
        Load configuration from a JSON file.
        
        Args:
            config_class: Configuration class
            file_path: JSON file path
            
        Returns:
            T: Configuration instance
        """
        with open(file_path, "r") as f:
            config_data = json.load(f)
        
        return config_class(**config_data)
    
    @staticmethod
    def from_yaml(config_class: Type[T], file_path: str) -> T:
        """
        Load configuration from a YAML file.
        
        Args:
            config_class: Configuration class
            file_path: YAML file path
            
        Returns:
            T: Configuration instance
        """
        with open(file_path, "r") as f:
            config_data = yaml.safe_load(f)
        
        return config_class(**config_data)
    
    @staticmethod
    def from_dict(config_class: Type[T], config_dict: Dict[str, Any]) -> T:
        """
        Load configuration from a dictionary.
        
        Args:
            config_class: Configuration class
            config_dict: Configuration dictionary
            
        Returns:
            T: Configuration instance
        """
        return config_class(**config_dict)
    
    @classmethod
    def load(
        cls,
        config_class: Type[T],
        env_prefix: str = "TEST_",
        json_path: Optional[str] = None,
        yaml_path: Optional[str] = None,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Load configuration from multiple sources with priority.
        
        Priority order:
        1. Environment variables
        2. JSON file
        3. YAML file
        4. Default values
        
        Args:
            config_class: Configuration class
            env_prefix: Environment variable prefix
            json_path: Optional JSON file path
            yaml_path: Optional YAML file path
            defaults: Optional default values
            
        Returns:
            T: Configuration instance
        """
        # Start with defaults
        config_dict = defaults or {}
        
        # Load from YAML file if provided
        if yaml_path and os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                yaml_dict = yaml.safe_load(f)
                if yaml_dict:
                    config_dict.update(yaml_dict)
        
        # Load from JSON file if provided
        if json_path and os.path.exists(json_path):
            with open(json_path, "r") as f:
                json_dict = json.load(f)
                config_dict.update(json_dict)
        
        # Load from environment variables
        env_vars = {
            k[len(env_prefix):].lower(): v
            for k, v in os.environ.items()
            if k.startswith(env_prefix)
        }
        
        # Convert values to appropriate types
        for key, value in env_vars.items():
            # Convert boolean strings
            if isinstance(value, str):
                if value.lower() in ("true", "yes", "1"):
                    env_vars[key] = True
                elif value.lower() in ("false", "no", "0"):
                    env_vars[key] = False
                
                # Convert numeric strings
                elif value.isdigit():
                    env_vars[key] = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    env_vars[key] = float(value)
        
        # Update config with environment variables
        config_dict.update(env_vars)
        
        # Create configuration instance
        return config_class(**config_dict)


class TestConfigManager:
    """
    Test configuration manager.
    
    This class provides utilities for managing test configurations for different environments.
    """
    
    def __init__(self, config_class: Type[T], env_prefix: str = "TEST_"):
        """
        Initialize the manager.
        
        Args:
            config_class: Configuration class
            env_prefix: Environment variable prefix
        """
        self.config_class = config_class
        self.env_prefix = env_prefix
        self.configs = {}
    
    def register_config(self, environment: str, config: T):
        """
        Register a configuration for an environment.
        
        Args:
            environment: Environment name
            config: Configuration instance
        """
        self.configs[environment] = config
    
    def get_config(self, environment: Optional[str] = None) -> T:
        """
        Get a configuration for an environment.
        
        Args:
            environment: Environment name (default: from environment variable)
            
        Returns:
            T: Configuration instance
        """
        # Get environment from environment variable if not provided
        if environment is None:
            environment = os.environ.get(f"{self.env_prefix}ENVIRONMENT", TestEnvironment.LOCAL)
        
        # Get configuration for environment
        if environment in self.configs:
            return self.configs[environment]
        
        # Load configuration from environment variables
        config = ConfigLoader.from_env(self.config_class, self.env_prefix)
        
        # Register configuration
        self.configs[environment] = config
        
        return config
    
    def load_configs(
        self,
        config_dir: str,
        environments: Optional[List[str]] = None,
        file_format: str = "json",
    ):
        """
        Load configurations from files.
        
        Args:
            config_dir: Configuration directory
            environments: Optional list of environments to load
            file_format: File format (json or yaml)
        """
        # Get environments to load
        if environments is None:
            environments = [
                TestEnvironment.LOCAL,
                TestEnvironment.DEVELOPMENT,
                TestEnvironment.STAGING,
                TestEnvironment.PRODUCTION,
            ]
        
        # Load configurations
        for environment in environments:
            file_path = os.path.join(config_dir, f"{environment}.{file_format}")
            
            if os.path.exists(file_path):
                if file_format == "json":
                    config = ConfigLoader.from_json(self.config_class, file_path)
                elif file_format == "yaml":
                    config = ConfigLoader.from_yaml(self.config_class, file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                self.register_config(environment, config)


# Example usage:
# 
# class MyTestConfig(BaseTestConfig):
#     # Add custom configuration fields
#     custom_field: str = "default value"
# 
# # Create a configuration manager
# config_manager = TestConfigManager(MyTestConfig)
# 
# # Load configurations from files
# config_manager.load_configs("config")
# 
# # Get configuration for current environment
# config = config_manager.get_config()
