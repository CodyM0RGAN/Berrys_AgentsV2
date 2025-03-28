"""
Model Orchestration API client.

This module provides a client for interacting with the Model Orchestration service,
which handles routing requests to appropriate AI models.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from shared.utils.src.clients.base import BaseAPIClient
from shared.utils.src.retry import retry_with_backoff, RetryPolicy
from shared.utils.src.exceptions import ServiceUnavailableError, MaxRetriesExceededError

# Set up logger
logger = logging.getLogger(__name__)

class ModelOrchestrationClient(BaseAPIClient):
    """
    Client for the Model Orchestration API.
    
    This client provides methods for interacting with the Model Orchestration service,
    which handles routing requests to appropriate AI models.
    """
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models.
        
        Returns:
            A list of model information dictionaries
        
        Raises:
            requests.RequestException: If the request fails
        """
        return self.get('/models')
    
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_id: The ID of the model to get
            
        Returns:
            A dictionary with model information
            
        Raises:
            requests.RequestException: If the request fails
        """
        return self.get(f'/models/{model_id}')
    
    async def generate_text(self, 
                     prompt: str, 
                     model_id: Optional[str] = None,
                     max_tokens: int = 1000,
                     temperature: float = 0.7,
                     top_p: float = 1.0,
                     frequency_penalty: float = 0.0,
                     presence_penalty: float = 0.0,
                     stop: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate text using a language model.
        
        Args:
            prompt: The prompt to generate text from
            model_id: The ID of the model to use (optional, will use default if not provided)
            max_tokens: The maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
            top_p: Controls diversity via nucleus sampling (0.0-1.0)
            frequency_penalty: Penalizes repeated tokens (0.0-2.0)
            presence_penalty: Penalizes repeated topics (0.0-2.0)
            stop: List of strings that stop generation when encountered
            
        Returns:
            A dictionary with the generated text and metadata
            
        Raises:
            requests.RequestException: If the request fails
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def generate_text_operation():
            payload = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': top_p,
                'frequency_penalty': frequency_penalty,
                'presence_penalty': presence_penalty
            }
            
            if model_id:
                payload['model_id'] = model_id
                
            if stop:
                payload['stop'] = stop
                
            return self.post('/generate', payload)

        try:
            return await retry_with_backoff(
                operation=generate_text_operation,
                policy=retry_policy,
                operation_name="generate_text"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to generate text after multiple retries: {e}")
            raise
    
    async def generate_chat_completion(self,
                               messages: List[Dict[str, str]],
                               model_id: Optional[str] = None,
                               max_tokens: int = 1000,
                               temperature: float = 0.7,
                               top_p: float = 1.0,
                               frequency_penalty: float = 0.0,
                               presence_penalty: float = 0.0,
                               stop: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a chat completion using a language model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model_id: The ID of the model to use (optional, will use default if not provided)
            max_tokens: The maximum number of tokens to generate
            temperature: Controls randomness (0.0-1.0)
            top_p: Controls diversity via nucleus sampling (0.0-1.0)
            frequency_penalty: Penalizes repeated tokens (0.0-2.0)
            presence_penalty: Penalizes repeated topics (0.0-2.0)
            stop: List of strings that stop generation when encountered
            
        Returns:
            A dictionary with the generated chat completion and metadata
            
        Raises:
            requests.RequestException: If the request fails
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def generate_chat_completion_operation():
            payload = {
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': top_p,
                'frequency_penalty': frequency_penalty,
                'presence_penalty': presence_penalty
            }
            
            if model_id:
                payload['model_id'] = model_id
                
            if stop:
                payload['stop'] = stop
                
            return self.post('/chat/completions', payload)

        try:
            return await retry_with_backoff(
                operation=generate_chat_completion_operation,
                policy=retry_policy,
                operation_name="generate_chat_completion"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to generate chat completion after multiple retries: {e}")
            raise
    
    async def generate_embeddings(self, 
                          texts: List[str],
                          model_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            model_id: The ID of the model to use (optional, will use default if not provided)
            
        Returns:
            A dictionary with the generated embeddings and metadata
            
        Raises:
            requests.RequestException: If the request fails
        """
        retry_policy = RetryPolicy(
            max_retries=3,
            base_delay=0.5,
            max_delay=4.0,
            retry_exceptions=[ServiceUnavailableError]
        )

        async def generate_embeddings_operation():
            payload = {
                'texts': texts
            }
            
            if model_id:
                payload['model_id'] = model_id
                
            return self.post('/embeddings', payload)

        try:
            return await retry_with_backoff(
                operation=generate_embeddings_operation,
                policy=retry_policy,
                operation_name="generate_embeddings"
            )
        except MaxRetriesExceededError as e:
            logger.error(f"Failed to generate embeddings after multiple retries: {e}")
            raise
    
    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for a specific model.
        
        Args:
            model_id: The ID of the model to get performance metrics for
            
        Returns:
            A dictionary with performance metrics
            
        Raises:
            requests.RequestException: If the request fails
        """
        return self.get(f'/models/{model_id}/performance')
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for all models.
        
        Returns:
            A dictionary with usage statistics
            
        Raises:
            requests.RequestException: If the request fails
        """
        return self.get('/usage')
