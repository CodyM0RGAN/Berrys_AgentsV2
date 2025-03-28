from typing import Optional, Dict, Any, List
from pydantic import Field

from shared.utils.src.config import BaseServiceConfig, load_config, Environment


class ModelOrchestrationConfig(BaseServiceConfig):
    """
    Configuration for the Model Orchestration service.
    """
    # Service information
    service_name: str = Field("model-orchestration", description="Service name")
    
    # Database configuration
    db_pool_size: int = Field(5, description="Database connection pool size")
    db_max_overflow: int = Field(10, description="Maximum number of connections to overflow")
    db_pool_timeout: int = Field(30, description="Seconds to wait before giving up on getting a connection")
    db_pool_recycle: int = Field(1800, description="Seconds after which a connection is recycled")
    
    # Authentication
    jwt_secret: str = Field("insecure-secret-key-for-development-only", description="Secret key for JWT")
    jwt_algorithm: str = Field("HS256", description="Algorithm for JWT")
    access_token_expire_minutes: int = Field(30, description="Minutes until access token expires")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_organization: Optional[str] = Field(None, description="OpenAI organization ID")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    
    # Ollama
    ollama_url: str = Field("http://ollama:11434", description="Ollama API URL")
    
    # Service URLs
    agent_orchestrator_url: Optional[str] = Field(None, description="Agent Orchestrator service URL")
    
    # Model configuration
    default_model: str = Field("gpt-3.5-turbo", description="Default model to use")
    default_provider: str = Field("openai", description="Default provider to use")
    default_timeout: float = Field(60.0, description="Default timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    
    # Token limits
    max_input_tokens: int = Field(8000, description="Maximum input tokens")
    max_output_tokens: int = Field(2000, description="Maximum output tokens")
    token_buffer_percentage: float = Field(0.1, description="Token buffer percentage")
    
    # Cost tracking
    enable_cost_tracking: bool = Field(True, description="Enable cost tracking")
    
    # Feature flags
    enable_fallback: bool = Field(True, description="Enable fallback to alternative models")
    enable_caching: bool = Field(False, description="Enable response caching")
    enable_streaming: bool = Field(True, description="Enable streaming responses")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(None, description="Sentry DSN for error reporting")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    
    def get_database_args(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy database connection arguments.

        Returns:
            A dictionary of database connection arguments.
        """
        args = super().get_database_args()
        args.update({
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_recycle": self.db_pool_recycle,
        })
        return args
    
    def get_model_config(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific model.

        Args:
            model_id: The model ID to get configuration for. If None, returns default configuration.

        Returns:
            A dictionary of model configuration.
        """
        # This would typically load from a database or configuration file
        # For now, just return default values
        return {
            "model_id": model_id or self.default_model,
            "provider": self.default_provider,
            "timeout": self.default_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "token_buffer_percentage": self.token_buffer_percentage,
        }
    
    def get_provider_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider: The provider to get configuration for. If None, returns default provider configuration.

        Returns:
            A dictionary of provider configuration.
        """
        provider = provider or self.default_provider
        
        if provider.upper() == "OPENAI":
            return {
                "api_key": self.openai_api_key,
                "organization": self.openai_organization,
            }
        elif provider.upper() == "ANTHROPIC":
            return {
                "api_key": self.anthropic_api_key,
            }
        elif provider.upper() == "OLLAMA":
            return {
                "url": self.ollama_url,
            }
        else:
            return {}


# Load configuration from environment variables
config = load_config(ModelOrchestrationConfig, "MODEL_ORCHESTRATION")

def get_settings() -> ModelOrchestrationConfig:
    """
    Get the application settings.
    
    Returns:
        ModelOrchestrationConfig: Application settings
    """
    return config
