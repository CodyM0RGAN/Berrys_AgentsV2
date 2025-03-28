"""
API request models.

This module contains the request models used by the model orchestration service API.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import Field, field_validator
import pydantic

from shared.models.src.base import BaseEntityModel, BaseModel # Added BaseModel import
from shared.models.src.enums import ModelProvider, RequestType
from shared.models.src.api.requests import ListRequestParams
from shared.models.src.chat import ChatMessage

__all__ = [
    "ListRequestParams",
    "RequestBase",
    "ChatRequest",
    "CompletionRequest",
    "EmbeddingRequest",
    "ImageGenerationRequest",
    "AudioTranscriptionRequest",
    "AudioTranslationRequest",
    "ModelRequest",
]


class RequestBase(BaseEntityModel):
    """
    Base model for a model request.
    """
    request_type: RequestType
    model_id: Optional[str] = None
    provider: Optional[ModelProvider] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stop: Optional[List[str]] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    task_type: Optional[str] = None  # e.g., 'code_generation', 'reasoning', 'creative'
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(RequestBase):
    """
    Model for a chat request.
    """
    request_type: RequestType = RequestType.CHAT
    messages: List[ChatMessage]
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "gpt-4",
                "messages": [
                    {
                        "role": "SYSTEM",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "USER",
                        "content": "Hello, how are you?"
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.7,
                "user_id": "user-123"
            }
        }
    }


class CompletionRequest(RequestBase):
    """
    Model for a completion request.
    """
    request_type: RequestType = RequestType.COMPLETION
    prompt: str
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "text-davinci-003",
                "prompt": "Once upon a time",
                "max_tokens": 100,
                "temperature": 0.7,
                "user_id": "user-123"
            }
        }
    }


class EmbeddingRequest(RequestBase):
    """
    Model for an embedding request.
    """
    request_type: RequestType = RequestType.EMBEDDING
    input: Union[str, List[str]]
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "text-embedding-ada-002",
                "input": "The food was delicious and the service was excellent.",
                "user_id": "user-123"
            }
        }
    }


class ImageGenerationRequest(RequestBase):
    """
    Model for an image generation request.
    """
    request_type: RequestType = RequestType.IMAGE_GENERATION
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"
    n: Optional[int] = 1
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "dall-e-3",
                "prompt": "A cute baby sea otter",
                "size": "1024x1024",
                "n": 1,
                "user_id": "user-123"
            }
        }
    }


class AudioTranscriptionRequest(RequestBase):
    """
    Model for an audio transcription request.
    """
    request_type: RequestType = RequestType.AUDIO_TRANSCRIPTION
    file_url: str
    language: Optional[str] = None
    prompt: Optional[str] = None
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "whisper-1",
                "file_url": "https://example.com/audio.mp3",
                "language": "en",
                "user_id": "user-123"
            }
        }
    }


class AudioTranslationRequest(RequestBase):
    """
    Model for an audio translation request.
    """
    request_type: RequestType = RequestType.AUDIO_TRANSLATION
    file_url: str
    prompt: Optional[str] = None
    
    model_config = {
        "schema_extra": {
            "example": {
                "model_id": "whisper-1",
                "file_url": "https://example.com/audio.mp3",
                "user_id": "user-123"
            }
        }
    }


class ModelRequest(BaseModel):
    """
    Union model for all request types.
    """
    request: Union[
        ChatRequest,
        CompletionRequest,
        EmbeddingRequest,
        ImageGenerationRequest,
        AudioTranscriptionRequest,
        AudioTranslationRequest,
    ]
