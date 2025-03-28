"""
Request processing functionality.

This module contains the RequestProcessingMixin class that provides methods for processing
different types of model requests.
"""

import logging
import time
import uuid
import httpx
from typing import Optional, Tuple, Dict, Any, List

from ...exceptions import (
    InvalidRequestError,
    ProviderNotAvailableError,
    TokenLimitError,
    RequestTimeoutError,
)
from shared.models.src.enums import AgentType
# Updated imports to use the correct modules
from ...models.api import (
    ChatRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    AudioTranscriptionRequest,
    AudioTranslationRequest,
    ModelResponseWrapper as ModelResponse,  # Renamed to match usage in this file
)

logger = logging.getLogger(__name__)


class RequestProcessingMixin:
    """
    Mixin for request processing operations.
    
    This mixin provides methods for processing different types of model requests:
    - Chat completion
    - Text completion
    - Embedding
    - Image generation
    - Audio transcription
    - Audio translation
    """
    
    async def _resolve_model_and_provider(self, model_id: Optional[str], provider: Optional[str]) -> Tuple[str, str]:
        """
        Resolve model ID and provider.
        
        Args:
            model_id: Model ID
            provider: Provider name
            
        Returns:
            Tuple[str, str]: Model ID and provider name
            
        Raises:
            InvalidRequestError: If model ID or provider cannot be resolved
        """
        # If model ID is provided, get the model and its provider
        if model_id:
            model = await self.get_model(model_id)
            if model:
                return model_id, model.provider.value
            
            # If provider is also provided, use it
            if provider:
                return model_id, provider
            
            # Otherwise, try to infer provider from model ID
            inferred_provider = self.provider_factory.infer_provider_from_model_id(model_id)
            if inferred_provider:
                return model_id, inferred_provider
            
            raise InvalidRequestError(f"Model '{model_id}' not found and provider not specified")
        
        # If only provider is provided, use default model for that provider
        if provider:
            default_model = self.provider_factory.get_default_model_for_provider(provider)
            if default_model:
                return default_model, provider
            
            raise InvalidRequestError(f"Provider '{provider}' has no default model")
        
        # If neither model ID nor provider is provided, use system default
        if self.settings.default_model_id and self.settings.default_provider:
            return self.settings.default_model_id, self.settings.default_provider
        
        raise InvalidRequestError("Model ID or provider must be specified")
    
    async def _check_token_limits(self, content: Any, model_id: str, provider: Any) -> None:
        """
        Check token limits for a request.
        
        Args:
            content: Request content
            model_id: Model ID
            provider: Provider
            
        Raises:
            TokenLimitError: If token limit is exceeded
        """
        # Get model token limit
        model = await self.get_model(model_id)
        token_limit = model.token_limit if model else None
        
        # If no token limit is set, skip check
        if not token_limit:
            return
        
        # Count tokens
        token_count = await provider.count_tokens(content)
        
        # Check if token count exceeds limit
        if token_count > token_limit:
            raise TokenLimitError(
                f"Token count {token_count} exceeds limit {token_limit} for model {model_id}"
            )
    
    async def _get_agent_specialization(self, agent_specialization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent specialization information from the Agent Orchestrator service.
        
        Args:
            agent_specialization_id: Agent specialization ID
            
        Returns:
            Optional[Dict[str, Any]]: Agent specialization information or None if not found
        """
        if not agent_specialization_id:
            return None
            
        try:
            # Get agent specialization from Agent Orchestrator
            agent_orchestrator_url = self.settings.agent_orchestrator_url
            if not agent_orchestrator_url:
                logger.warning("Agent Orchestrator URL not configured, skipping specialization lookup")
                return None
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{agent_orchestrator_url}/api/specializations/{agent_specialization_id}",
                    timeout=5.0,
                )
                
                if response.status_code == 200:
                    return response.json().get("data")
                elif response.status_code == 404:
                    logger.warning(f"Agent specialization {agent_specialization_id} not found")
                    return None
                else:
                    logger.error(f"Error getting agent specialization: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error getting agent specialization: {str(e)}")
            return None
    
    async def _enhance_request_with_specialization(self, request: Any) -> None:
        """
        Enhance a request with agent specialization information.
        
        Args:
            request: Request to enhance
        """
        if not hasattr(request, "agent_specialization_id") or not request.agent_specialization_id:
            return
            
        # Get agent specialization
        specialization = await self._get_agent_specialization(request.agent_specialization_id)
        if not specialization:
            return
            
        # Enhance request based on specialization
        if isinstance(request, ChatRequest):
            # Add specialization information to system message
            system_message_found = False
            for message in request.messages:
                if message.role.value == "SYSTEM":
                    system_message_found = True
                    # Enhance system message with specialization information
                    skills = specialization.get("required_skills", [])
                    responsibilities = specialization.get("responsibilities", [])
                    knowledge_domains = specialization.get("knowledge_domains", [])
                    
                    specialization_info = (
                        f"\n\nYou are specialized as a {specialization.get('agent_type', 'GENERAL')} agent with the following:\n"
                        f"Skills: {', '.join(skills)}\n"
                        f"Responsibilities: {', '.join(responsibilities)}\n"
                        f"Knowledge Domains: {', '.join(knowledge_domains)}"
                    )
                    
                    message.content += specialization_info
                    break
                    
            # If no system message found, add one
            if not system_message_found and request.messages:
                from ...models.api import ChatMessage, MessageRole
                
                # Create specialization information
                skills = specialization.get("required_skills", [])
                responsibilities = specialization.get("responsibilities", [])
                knowledge_domains = specialization.get("knowledge_domains", [])
                
                specialization_info = (
                    f"You are specialized as a {specialization.get('agent_type', 'GENERAL')} agent with the following:\n"
                    f"Skills: {', '.join(skills)}\n"
                    f"Responsibilities: {', '.join(responsibilities)}\n"
                    f"Knowledge Domains: {', '.join(knowledge_domains)}"
                )
                
                # Add system message at the beginning
                request.messages.insert(0, ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=specialization_info,
                ))
        elif isinstance(request, CompletionRequest):
            # Add specialization information to prompt
            skills = specialization.get("required_skills", [])
            responsibilities = specialization.get("responsibilities", [])
            knowledge_domains = specialization.get("knowledge_domains", [])
            
            specialization_info = (
                f"[You are specialized as a {specialization.get('agent_type', 'GENERAL')} agent with the following:\n"
                f"Skills: {', '.join(skills)}\n"
                f"Responsibilities: {', '.join(responsibilities)}\n"
                f"Knowledge Domains: {', '.join(knowledge_domains)}]\n\n"
            )
            
            request.prompt = specialization_info + request.prompt
    
    async def process_chat_request(self, request: ChatRequest) -> ModelResponse:
        """
        Process a chat request.
        
        Args:
            request: Chat request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Enhance request with specialization information
            await self._enhance_request_with_specialization(request)
            
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Check token limits
            if self.settings.enable_token_counting:
                await self._check_token_limits(request.messages, model_id, provider)
            
            # Process request
            response = await provider.chat_completion(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = None
            
            if self.settings.enable_cost_tracking and response.usage:
                cost = provider.calculate_cost(
                    model_id,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
            
            # Estimate quality score and confidence
            # This is a simple heuristic and could be improved with more sophisticated methods
            quality_score = None
            confidence = None
            
            if len(response.choices) > 0:
                # Estimate confidence based on finish reason
                # 'stop' is a good sign, 'length' might indicate truncation
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'stop':
                    confidence = 0.9  # High confidence
                elif finish_reason == 'length':
                    confidence = 0.7  # Medium confidence
                else:
                    confidence = 0.5  # Low confidence
            
            # Record performance metrics if performance tracker is available
            if self.performance_tracker and request.task_type:
                await self.performance_tracker.record_request_result(
                    request_id=request_id,
                    model_id=model_id,
                    task_type=request.task_type,
                    success=True,  # Assume success if no exception
                    quality_score=quality_score,
                    confidence=confidence,
                    metadata={
                        "latency_ms": latency_ms,
                        "tokens": response.usage.total_tokens if response.usage else None,
                    },
                )
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=cost,
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing chat request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, TokenLimitError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process chat request: {str(e)}")
    
    async def process_completion_request(self, request: CompletionRequest) -> ModelResponse:
        """
        Process a completion request.
        
        Args:
            request: Completion request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Enhance request with specialization information
            await self._enhance_request_with_specialization(request)
            
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Check token limits
            if self.settings.enable_token_counting:
                await self._check_token_limits(request.prompt, model_id, provider)
            
            # Process request
            response = await provider.text_completion(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = None
            
            if self.settings.enable_cost_tracking and response.usage:
                cost = provider.calculate_cost(
                    model_id,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=cost,
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing completion request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, TokenLimitError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process completion request: {str(e)}")
    
    async def process_embedding_request(self, request: EmbeddingRequest) -> ModelResponse:
        """
        Process an embedding request.
        
        Args:
            request: Embedding request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Process request
            response = await provider.embedding(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            cost = None
            
            if self.settings.enable_cost_tracking and response.usage:
                cost = provider.calculate_cost(
                    model_id,
                    response.usage.prompt_tokens,
                    0,  # No completion tokens for embeddings
                )
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=cost,
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing embedding request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, TokenLimitError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process embedding request: {str(e)}")
    
    async def process_image_generation_request(self, request: ImageGenerationRequest) -> ModelResponse:
        """
        Process an image generation request.
        
        Args:
            request: Image generation request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Process request
            response = await provider.image_generation(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=None,  # Cost calculation for images is more complex
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing image generation request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process image generation request: {str(e)}")
    
    async def process_audio_transcription_request(self, request: AudioTranscriptionRequest) -> ModelResponse:
        """
        Process an audio transcription request.
        
        Args:
            request: Audio transcription request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Process request
            response = await provider.audio_transcription(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=None,  # Cost calculation for audio is more complex
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing audio transcription request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process audio transcription request: {str(e)}")
    
    async def process_audio_translation_request(self, request: AudioTranslationRequest) -> ModelResponse:
        """
        Process an audio translation request.
        
        Args:
            request: Audio translation request
            
        Returns:
            ModelResponse: Model response
            
        Raises:
            InvalidRequestError: If request is invalid
            ProviderNotAvailableError: If provider is not available
            RequestTimeoutError: If request times out
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Get model and provider
            model_id, provider_name = await self._resolve_model_and_provider(request.model_id, request.provider)
            
            # Get provider
            provider = await self.provider_factory.get_provider(provider_name)
            
            # Process request
            response = await provider.audio_translation(request)
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Create response
            model_response = ModelResponse(
                response=response,
                request_id=request_id,
                model_id=model_id,
                provider=provider_name,
                latency_ms=latency_ms,
                cost=None,  # Cost calculation for audio is more complex
            )
            
            return model_response
        except Exception as e:
            logger.error(f"Error processing audio translation request: {str(e)}")
            
            # Publish error event
            await self.event_bus.publish_event(
                "model.request.failed",
                {
                    "request_id": request_id,
                    "model_id": request.model_id,
                    "error": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
            
            # Re-raise specific exceptions
            if isinstance(e, (InvalidRequestError, ProviderNotAvailableError, RequestTimeoutError)):
                raise
            
            # Wrap other exceptions
            raise InvalidRequestError(f"Failed to process audio translation request: {str(e)}")
