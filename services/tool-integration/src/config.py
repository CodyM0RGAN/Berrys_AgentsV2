from pydantic import Field
from pydantic_settings import SettingsConfigDict
from shared.utils.src.config import BaseServiceConfig, get_settings

class ToolIntegrationSettings(BaseServiceConfig):
    """Tool Integration service configuration settings."""
    
    # Service settings
    service_name: str = Field(
        "tool-integration", 
        description="Service name"
    )
    
    # API settings
    api_prefix: str = Field(
        "/api/v1", 
        description="API prefix"
    )
    
    # Tool execution settings
    execution_timeout: int = Field(
        30000, 
        description="Tool execution timeout in milliseconds"
    )
    max_concurrent_executions: int = Field(
        10, 
        description="Maximum number of concurrent tool executions"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

# Create a singleton instance
settings = get_settings(ToolIntegrationSettings)
