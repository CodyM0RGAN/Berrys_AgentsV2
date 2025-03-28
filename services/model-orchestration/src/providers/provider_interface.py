from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

from ..models.api import (
    ChatRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    AudioTranscriptionRequest,
    AudioTranslationRequest,
    ChatResponse,
    CompletionResponse,
    EmbeddingResponse,
    ImageGenerationResponse,
    AudioTranscriptionResponse,
    AudioTranslationResponse,
)


class ModelProvider(ABC):
    """
    Abstract base class for model providers.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            str: Provider name
        """
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the available models for this provider.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of model ID to model info
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the provider.
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the API key.
        
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Send a chat completion request.
        
        Args:
            request: Chat request
            
        Returns:
            ChatResponse: Chat response
        """
        pass
    
    @abstractmethod
    async def text_completion(
        self,
        request: CompletionRequest,
    ) -> CompletionResponse:
        """
        Send a text completion request.
        
        Args:
            request: Completion request
            
        Returns:
            CompletionResponse: Completion response
        """
        pass
    
    @abstractmethod
    async def embedding(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse:
        """
        Send an embedding request.
        
        Args:
            request: Embedding request
            
        Returns:
            EmbeddingResponse: Embedding response
        """
        pass
    
    @abstractmethod
    async def image_generation(
        self,
        request: ImageGenerationRequest,
    ) -> ImageGenerationResponse:
        """
        Send an image generation request.
        
        Args:
            request: Image generation request
            
        Returns:
            ImageGenerationResponse: Image generation response
        """
        pass
    
    @abstractmethod
    async def audio_transcription(
        self,
        request: AudioTranscriptionRequest,
    ) -> AudioTranscriptionResponse:
        """
        Send an audio transcription request.
        
        Args:
            request: Audio transcription request
            
        Returns:
            AudioTranscriptionResponse: Audio transcription response
        """
        pass
    
    @abstractmethod
    async def audio_translation(
        self,
        request: AudioTranslationRequest,
    ) -> AudioTranslationResponse:
        """
        Send an audio translation request.
        
        Args:
            request: Audio translation request
            
        Returns:
            AudioTranslationResponse: Audio translation response
        """
        pass
    
    @abstractmethod
    async def count_tokens(
        self,
        text: Union[str, List[Dict[str, str]]],
        model_id: str,
    ) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            model_id: Model ID
            
        Returns:
            int: Number of tokens
        """
        pass
    
    @abstractmethod
    def get_model_info(
        self,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Optional[Dict[str, Any]]: Model information or None if not found
        """
        pass
    
    @abstractmethod
    def supports_model(
        self,
        model_id: str,
    ) -> bool:
        """
        Check if the provider supports a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            bool: True if supported, False otherwise
        """
        pass
    
    @abstractmethod
    def calculate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculate the cost of a request.
        
        Args:
            model_id: Model ID
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            float: Cost in USD
        """
        pass
