"""
Planning System Service configuration.

This module defines the service configuration using shared configuration utilities,
providing strong typing and validation for configuration values.
"""

from typing import List

from shared.utils.src.config import BaseServiceConfig, load_config

class PlanningSystemConfig(BaseServiceConfig):
    """Planning System service configuration settings"""
    
    # Service information
    service_name: str = "planning-system"
    
    # API settings
    api_prefix: str = ""
    cors_origins: List[str] = ["*"]
    
    # Planning system specific settings
    max_task_depth: int = 10  # Maximum depth of task breakdown
    max_dependency_chain: int = 50  # Maximum length of dependency chain
    default_planning_horizon: int = 90  # Default planning horizon in days
    resource_optimization_timeout: int = 30  # Timeout for resource optimization in seconds
    forecasting_confidence_interval: float = 0.8  # Confidence interval for forecasting (0.0-1.0)
    
    # NetworkX settings
    dependency_cycle_detection: bool = True  # Detect cycles in dependency graphs
    
    # Cache settings
    plan_cache_ttl: int = 600  # Time to live for plan cache in seconds
    forecast_cache_ttl: int = 3600  # Time to live for forecast cache in seconds
    
    # Default solver for resource optimization
    default_solver: str = "pulp"  # Options: pulp, ortools
    
    # Model config
    model_config = {
        "env_prefix": "PLANNING_",
    }

# Load configuration from environment variables
config = load_config(PlanningSystemConfig, "PLANNING")

def get_settings() -> PlanningSystemConfig:
    """
    Get the application settings.
    
    Returns:
        PlanningSystemConfig: Application settings
    """
    return config
