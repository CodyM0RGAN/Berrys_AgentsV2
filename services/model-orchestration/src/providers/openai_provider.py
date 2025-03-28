import logging
import time
import json
from typing import Dict, Any, List, Optional, Union, Tuple
import asyncio
from datetime import datetime

import openai
import tiktoken
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import Settings
from ..exceptions import (
    ProviderAuthenticationError,
    ProviderNotAvailableError,
    RateLimitError,
    TokenLimitError,
    RequestTimeoutError,
    ContentFilterError,
    InvalidRequestError,
)
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
    ChatMessage,
    MessageRole,
    ChatResponseChoice,
    CompletionResponseChoice,
    EmbeddingResponseData,
    ImageResponseData,
    TokenUsage,
)
from .provider_interface import ModelProvider as ModelProviderInterface

logger = logging.getLogger(__name__)


class OpenAIProvider(ModelProviderInterface):
    """
    OpenAI provider implementation.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the OpenAI provider.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = None
        self._available_models = {}
        self._encoders = {}
    
    @property
    def provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            str: Provider name
        """
        return "openai"
    
    @property
    def available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the available models for this provider.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of model ID to model info
        """
        return self._available_models
    
    async def initialize(self) -> None:
        """
        Initialize the provider.
        """
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=self.settings.openai_api_key,
            organization=self.settings.openai_organization,
            timeout=self.settings.default_timeout,
        )
        
        # Initialize available models
        await self._initialize_models()
    
    async def validate_api_key(self) -> bool:
        """
        Validate the API key.
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.settings.openai_api_key:
            logger.warning("OpenAI API key not provided")
            return False
        
        try:
            # Try to list models
            await self.client.model.list()
            return True
        except openai.AuthenticationError:
            logger.error("Invalid OpenAI API key")
            return False
        except Exception as e:
            logger.error(f"Error validating OpenAI API key: {str(e)}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
            ContentFilterError: If content is filtered
            InvalidRequestError: If request is invalid
        """
        try:
            # Convert messages to OpenAI format
            messages = []
            for message in request.messages:
                openai_message = {
                    "role": message.role.value,
                    "content": message.content,
                }
                
                if message.name:
                    openai_message["name"] = message.name
                
                if message.tool_calls:
                    openai_message["tool_calls"] = message.tool_calls
                
                if message.tool_call_id:
                    openai_message["tool_call_id"] = message.tool_call_id
                
                messages.append(openai_message)
            
            # Prepare request parameters
            params = {
                "model": request.model_id,
                "messages": messages,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            }
            
            if request.max_tokens:
                params["max_tokens"] = request.max_tokens
            
            if request.stop:
                params["stop"] = request.stop
            
            if request.user_id:
                params["user"] = request.user_id
            
            # Send request
            response = await self.client.chat.completions.create(**params)
            
            # Convert response to our format
            choices = []
            for i, choice in enumerate(response.choices):
                message = ChatMessage(
                    role=MessageRole(choice.message.role),
                    content=choice.message.content,
                )
                
                choices.append(
                    ChatResponseChoice(
                        index=i,
                        message=message,
                        finish_reason=choice.finish_reason,
                    )
                )
            
            # Create usage
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            
            # Create response
            chat_response = ChatResponse(
                id=response.id,
                object="chat.completion",
                created=int(datetime.now().timestamp()),
                model=response.model,
                choices=choices,
                usage=usage,
            )
            
            return chat_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            if "content filter" in str(e).lower():
                raise ContentFilterError(str(e))
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
            ContentFilterError: If content is filtered
            InvalidRequestError: If request is invalid
        """
        try:
            # For newer models, use chat completion API with a single user message
            if request.model_id.startswith("gpt-"):
                # Convert to chat request
                chat_request = ChatRequest(
                    model_id=request.model_id,
                    messages=[
                        ChatMessage(
                            role=MessageRole.USER,
                            content=request.prompt,
                        )
                    ],
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    frequency_penalty=request.frequency_penalty,
                    presence_penalty=request.presence_penalty,
                    stop=request.stop,
                    user_id=request.user_id,
                )
                
                # Send chat request
                chat_response = await self.chat_completion(chat_request)
                
                # Convert to completion response
                choices = []
                for i, choice in enumerate(chat_response.choices):
                    choices.append(
                        CompletionResponseChoice(
                            index=i,
                            text=choice.message.content,
                            finish_reason=choice.finish_reason,
                        )
                    )
                
                # Create response
                completion_response = CompletionResponse(
                    id=chat_response.id,
                    object="text_completion",
                    created=chat_response.created,
                    model=chat_response.model,
                    choices=choices,
                    usage=chat_response.usage,
                )
                
                return completion_response
            
            # For legacy models, use completions API
            # Prepare request parameters
            params = {
                "model": request.model_id,
                "prompt": request.prompt,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            }
            
            if request.max_tokens:
                params["max_tokens"] = request.max_tokens
            
            if request.stop:
                params["stop"] = request.stop
            
            if request.user_id:
                params["user"] = request.user_id
            
            # Send request
            response = await self.client.completions.create(**params)
            
            # Convert response to our format
            choices = []
            for i, choice in enumerate(response.choices):
                choices.append(
                    CompletionResponseChoice(
                        index=i,
                        text=choice.text,
                        finish_reason=choice.finish_reason,
                    )
                )
            
            # Create usage
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            
            # Create response
            completion_response = CompletionResponse(
                id=response.id,
                object="text_completion",
                created=int(datetime.now().timestamp()),
                model=response.model,
                choices=choices,
                usage=usage,
            )
            
            return completion_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            if "content filter" in str(e).lower():
                raise ContentFilterError(str(e))
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI text completion: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            TokenLimitError: If token limit is exceeded
            RequestTimeoutError: If request times out
            InvalidRequestError: If request is invalid
        """
        try:
            # Prepare request parameters
            params = {
                "model": request.model_id or "text-embedding-ada-002",
                "input": request.input,
            }
            
            if request.user_id:
                params["user"] = request.user_id
            
            # Send request
            response = await self.client.embeddings.create(**params)
            
            # Convert response to our format
            data = []
            for i, embedding in enumerate(response.data):
                data.append(
                    EmbeddingResponseData(
                        index=i,
                        embedding=embedding.embedding,
                    )
                )
            
            # Create usage
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=0,
                total_tokens=response.usage.total_tokens,
            )
            
            # Create response
            embedding_response = EmbeddingResponse(
                object="embedding",
                model=response.model,
                data=data,
                usage=usage,
            )
            
            return embedding_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI embedding: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            RequestTimeoutError: If request times out
            ContentFilterError: If content is filtered
            InvalidRequestError: If request is invalid
        """
        try:
            # Prepare request parameters
            params = {
                "model": request.model_id or "dall-e-3",
                "prompt": request.prompt,
                "n": request.n or 1,
            }
            
            if request.size:
                params["size"] = request.size
            
            if request.quality:
                params["quality"] = request.quality
            
            if request.user_id:
                params["user"] = request.user_id
            
            # Send request
            response = await self.client.images.generate(**params)
            
            # Convert response to our format
            data = []
            for i, image in enumerate(response.data):
                data.append(
                    ImageResponseData(
                        url=image.url,
                        revised_prompt=image.revised_prompt,
                    )
                )
            
            # Create response
            image_response = ImageGenerationResponse(
                created=int(datetime.now().timestamp()),
                data=data,
            )
            
            return image_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            if "content filter" in str(e).lower():
                raise ContentFilterError(str(e))
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI image generation: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            RequestTimeoutError: If request times out
            InvalidRequestError: If request is invalid
        """
        try:
            # Prepare request parameters
            params = {
                "model": request.model_id or "whisper-1",
                "file": request.file_url,
            }
            
            if request.language:
                params["language"] = request.language
            
            if request.prompt:
                params["prompt"] = request.prompt
            
            # Send request
            response = await self.client.audio.transcriptions.create(**params)
            
            # Create response
            transcription_response = AudioTranscriptionResponse(
                text=response.text,
            )
            
            return transcription_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI audio transcription: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        reraise=True,
    )
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
            
        Raises:
            ProviderAuthenticationError: If authentication fails
            ProviderNotAvailableError: If provider is not available
            RateLimitError: If rate limit is exceeded
            RequestTimeoutError: If request times out
            InvalidRequestError: If request is invalid
        """
        try:
            # Prepare request parameters
            params = {
                "model": request.model_id or "whisper-1",
                "file": request.file_url,
            }
            
            if request.prompt:
                params["prompt"] = request.prompt
            
            # Send request
            response = await self.client.audio.translations.create(**params)
            
            # Create response
            translation_response = AudioTranslationResponse(
                text=response.text,
            )
            
            return translation_response
        except openai.AuthenticationError as e:
            raise ProviderAuthenticationError(self.provider_name, str(e))
        except openai.RateLimitError as e:
            raise RateLimitError(self.provider_name, str(e))
        except openai.APITimeoutError as e:
            raise RequestTimeoutError(self.provider_name, str(e))
        except openai.BadRequestError as e:
            raise InvalidRequestError(str(e))
        except openai.APIError as e:
            raise ProviderNotAvailableError(self.provider_name, str(e))
        except Exception as e:
            logger.error(f"Error in OpenAI audio translation: {str(e)}")
            raise ProviderNotAvailableError(self.provider_name, f"Unexpected error: {str(e)}")
    
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
        # Get encoding for model
        encoding = self._get_encoding(model_id)
        
        # Count tokens
        if isinstance(text, str):
            return len(encoding.encode(text))
        elif isinstance(text, list):
            # For chat messages
            token_count = 0
            
            for message in text:
                # Add tokens for role
                token_count += 4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
                
                # Add tokens for name if present
                if "name" in message:
                    token_count += len(encoding.encode(message["name"]))
                
                # Add tokens for content
                if "content" in message and message["content"]:
                    token_count += len(encoding.encode(message["content"]))
            
            # Add tokens for assistant reply
            token_count += 2  # Every reply is <im_start>assistant
            
            return token_count
        else:
            raise ValueError(f"Unsupported text type: {type(text)}")
    
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
        return self._available_models.get(model_id)
    
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
        # Check if model is in available models
        if model_id in self._available_models:
            return True
        
        # Check if model ID starts with a known prefix
        if model_id.startswith("gpt-") or model_id.startswith("text-") or model_id.startswith("dall-e"):
            return True
        
        return False
    
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
        # Get model info
        model_info = self.get_model_info(model_id)
        
        # If model info is not available, use default pricing
        if not model_info or "pricing" not in model_info:
            # Default pricing for GPT-3.5-turbo
            if model_id.startswith("gpt-3.5"):
                return (prompt_tokens * 0.0000015) + (completion_tokens * 0.000002)
            # Default pricing for GPT-4
            elif model_id.startswith("gpt-4"):
                return (prompt_tokens * 0.00003) + (completion_tokens * 0.00006)
            # Default pricing for embeddings
            elif model_id.startswith("text-embedding"):
                return prompt_tokens * 0.0000001
            # Default pricing for DALL-E
            elif model_id.startswith("dall-e"):
                return 0.02  # $0.02 per image for DALL-E 2
            # Default pricing for Whisper
            elif model_id.startswith("whisper"):
                return 0.006  # $0.006 per minute
            # Unknown model
            else:
                return 0.0
        
        # Use model-specific pricing
        pricing = model_info["pricing"]
        prompt_cost = pricing.get("prompt", 0.0) * prompt_tokens / 1000
        completion_cost = pricing.get("completion", 0.0) * completion_tokens / 1000
        
        return prompt_cost + completion_cost
    
    async def _initialize_models(self) -> None:
        """
        Initialize available models.
        """
        try:
            # Get models from OpenAI
            response = await self.client.model.list()
            
            # Process models
            for model in response.data:
                model_id = model.id
                
                # Skip non-relevant models
                if not (
                    model_id.startswith("gpt-")
                    or model_id.startswith("text-")
                    or model_id.startswith("dall-e")
                    or model_id.startswith("whisper")
                ):
                    continue
                
                # Determine capabilities
                capabilities = []
                
                if model_id.startswith("gpt-"):
                    capabilities.append("chat")
                    capabilities.append("completion")
                elif model_id.startswith("text-embedding"):
                    capabilities.append("embedding")
                elif model_id.startswith("dall-e"):
                    capabilities.append("image_generation")
                elif model_id.startswith("whisper"):
                    capabilities.append("audio_transcription")
                    capabilities.append("audio_translation")
                
                # Determine token limits
                token_limit = None
                
                if "gpt-3.5-turbo" in model_id:
                    token_limit = 4096
                elif "gpt-4" in model_id:
                    if "32k" in model_id:
                        token_limit = 32768
                    else:
                        token_limit = 8192
                
                # Determine pricing
                pricing = {}
                
                if "gpt-3.5-turbo" in model_id:
                    pricing = {
                        "prompt": 0.0015,  # $0.0015 per 1K tokens
                        "completion": 0.002,  # $0.002 per 1K tokens
                    }
                elif "gpt-4" in model_id:
                    pricing = {
                        "prompt": 0.03,  # $0.03 per 1K tokens
                        "completion": 0.06,  # $0.06 per 1K tokens
                    }
                elif "text-embedding" in model_id:
                    pricing = {
                        "prompt": 0.0001,  # $0.0001 per 1K tokens
                        "completion": 0.0,
                    }
                
                # Add model to available models
                self._available_models[model_id] = {
                    "id": model_id,
                    "provider": self.provider_name,
                    "capabilities": capabilities,
                    "token_limit": token_limit,
                    "pricing": pricing,
                }
            
            logger.info(f"Initialized {len(self._available_models)} OpenAI models")
        except Exception as e:
            logger.error(f"Error initializing OpenAI models: {str(e)}")
            # Continue with empty models list
    
    def _get_encoding(self, model_id: str) -> Any:
        """
        Get the encoding for a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Any: Encoding
        """
        # Check if encoding is already cached
        if model_id in self._encoders:
            return self._encoders[model_id]
        
        # Get encoding name for model
        if model_id.startswith("gpt-4"):
            encoding_name = "cl100k_base"
        elif model_id.startswith("gpt-3.5-turbo"):
            encoding_name = "cl100k_base"
        elif model_id.startswith("text-embedding-ada"):
            encoding_name = "cl100k_base"
        else:
            # Default to p50k_base for other models
            encoding_name = "p50k_base"
        
        # Get encoding
        try:
            encoding = tiktoken.get_encoding(encoding_name)
        except KeyError:
            # Fallback to p50k_base
            encoding = tiktoken.get_encoding("p50k_base")
        
        # Cache encoding
        self._encoders[model_id] = encoding
        
        return encoding
