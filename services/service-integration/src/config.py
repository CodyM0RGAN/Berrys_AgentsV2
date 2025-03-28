"""
Configuration management for the Service Integration service.

This module provides configuration settings and utilities for the Service Integration service.
"""
from shared.utils.src.config import BaseServiceConfig, load_config

class ServiceIntegrationConfig(BaseServiceConfig):
    """Configuration settings for the Service Integration service."""
    
    # Service-specific configuration
    service_name: str = "service-integration"
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_timeout: int = 60  # seconds
    circuit_breaker_half_open_max_calls: int = 3
    
    # Workflow settings
    workflow_execution_timeout: int = 3600  # 1 hour
    max_concurrent_workflows: int = 10
    
    # Service discovery settings
    service_heartbeat_interval: int = 30  # seconds
    service_offline_threshold: int = 90  # seconds
    
    # Retry settings
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 1.5
    
    # Logging settings
    log_level: str = "INFO"
    enable_request_logging: bool = True
    
    def get_circuit_breaker_settings(self):
        """Get circuit breaker settings as a dictionary."""
        return {
            "failure_threshold": self.circuit_breaker_failure_threshold,
            "reset_timeout": self.circuit_breaker_reset_timeout,
            "half_open_max_calls": self.circuit_breaker_half_open_max_calls
        }
    
    def get_workflow_settings(self):
        """Get workflow settings as a dictionary."""
        return {
            "execution_timeout": self.workflow_execution_timeout,
            "max_concurrent_workflows": self.max_concurrent_workflows
        }
    
    def get_service_discovery_settings(self):
        """Get service discovery settings as a dictionary."""
        return {
            "heartbeat_interval": self.service_heartbeat_interval,
            "offline_threshold": self.service_offline_threshold
        }
    
    def get_retry_settings(self):
        """Get retry settings as a dictionary."""
        return {
            "max_attempts": self.max_retry_attempts,
            "backoff_factor": self.retry_backoff_factor
        }

# Load configuration from environment variables
config = load_config(ServiceIntegrationConfig, "SERVICE_INTEGRATION")

def get_settings() -> ServiceIntegrationConfig:
    """
    Get the application settings.
    
    Returns:
        ServiceIntegrationConfig: Application settings
    """
    return config
