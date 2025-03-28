import logging
from typing import Dict, Any, Optional, List, Type

from ..config import ModelOrchestrationConfig, config
from ..exceptions import ProviderNotAvailableError
# Corrected import location for ModelProviderEnum
from shared.models.src.enums import ModelProvider as ModelProviderEnum
from .provider_interface import ModelProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for creating and managing provider instances.
    """
    
    def __init__(self, settings: ModelOrchestrationConfig):
        """
        Initialize the provider factory.
        
        Args:
            settings: Application settings
        """
        self.settings = config
        self.providers: Dict[str, ModelProvider] = {}
        self.provider_classes: Dict[str, Type[ModelProvider]] = {}
    
    def register_provider_class(self, provider_name: str, provider_class: Type[ModelProvider]) -> None:
        """
        Register a provider class.
        
        Args:
            provider_name: Provider name
            provider_class: Provider class
        """
        self.provider_classes[provider_name] = provider_class
        logger.info(f"Registered provider class: {provider_name}")
    
    async def get_provider(self, provider_name: str) -> ModelProvider:
        """
        Get a provider instance.
        
        Args:
            provider_name: Provider name
            
        Returns:
            ModelProvider: Provider instance
            
        Raises:
            ProviderNotAvailableError: If provider is not available
        """
        # Convert to lowercase for case-insensitive comparison
        provider_name = provider_name.lower()
        
        # Check if provider is already initialized
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        # Check if provider class is registered
        if provider_name not in self.provider_classes:
            raise ProviderNotAvailableError(provider_name, f"Provider '{provider_name}' is not registered")
        
        # Create provider instance
        provider_class = self.provider_classes[provider_name]
        provider = provider_class(self.settings)
        
        # Initialize provider
        try:
            await provider.initialize()
            
            # Validate API key
            if not await provider.validate_api_key():
                logger.warning(f"API key validation failed for provider: {provider_name}")
            
            # Store provider instance
            self.providers[provider_name] = provider
            logger.info(f"Initialized provider: {provider_name}")
            
            return provider
        except Exception as e:
            logger.error(f"Failed to initialize provider '{provider_name}': {str(e)}")
            raise ProviderNotAvailableError(provider_name, f"Failed to initialize provider: {str(e)}")
    
    async def get_all_providers(self) -> List[ModelProvider]:
        """
        Get all available provider instances.
        
        Returns:
            List[ModelProvider]: List of provider instances
        """
        providers = []
        
        for provider_name in self.provider_classes.keys():
            try:
                provider = await self.get_provider(provider_name)
                providers.append(provider)
            except ProviderNotAvailableError:
                # Skip unavailable providers
                pass
        
        return providers
    
    def get_provider_for_model(self, model_id: str) -> Optional[str]:
        """
        Get the provider name for a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[str]: Provider name or None if not found
        """
        # Check each provider
        for provider_name, provider in self.providers.items():
            if provider.supports_model(model_id):
                return provider_name
        
        # Check model ID prefix
        if model_id.startswith("gpt-") or model_id.startswith("text-") or model_id.startswith("dall-e"):
            return ModelProviderEnum.OPENAI.value
        elif model_id.startswith("claude-"):
            return ModelProviderEnum.ANTHROPIC.value
        
        return None


# Singleton instance
_provider_factory: Optional[ProviderFactory] = None


def get_provider_factory(settings: ModelOrchestrationConfig) -> ProviderFactory:
    """
    Get the provider factory singleton instance.
    
    Args:
        settings: Application settings
        
    Returns:
        ProviderFactory: Provider factory instance
    """
    global _provider_factory
    
    if _provider_factory is None:
        _provider_factory = ProviderFactory(config)
        
        # Import provider implementations
        # This is done here to avoid circular imports
        try:
            from .openai_provider import OpenAIProvider
            _provider_factory.register_provider_class(ModelProviderEnum.OPENAI.value, OpenAIProvider)
        except ImportError:
            logger.warning("OpenAI provider not available")
        
        try:
            from .anthropic_provider import AnthropicProvider
            _provider_factory.register_provider_class(ModelProviderEnum.ANTHROPIC.value, AnthropicProvider)
        except ImportError:
            logger.warning("Anthropic provider not available")
        
        try:
            from .ollama_provider import OllamaProvider
            _provider_factory.register_provider_class(ModelProviderEnum.OLLAMA.value, OllamaProvider)
        except ImportError:
            logger.warning("Ollama provider not available")
    
    return _provider_factory
