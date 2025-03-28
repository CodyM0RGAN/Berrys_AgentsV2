"""
API response models.

This module contains the response models used by the model orchestration service API.
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel

# Corrected import location
from shared.models.src.api.responses import create_data_response_model, create_list_response_model
from shared.models.src.chat import ChatMessage

__all__ = [
    "create_data_response_model",
    "create_list_response_model",
    "TokenUsage",
    "ChatResponseChoice",
    "CompletionResponseChoice",
    "EmbeddingResponseData",
    "ImageResponseData",
    "ChatResponse",
    "CompletionResponse",
    "EmbeddingResponse",
    "ImageGenerationResponse",
    "AudioTranscriptionResponse",
    "AudioTranslationResponse",
    "ModelResponseWrapper",
]


class TokenUsage(BaseModel):
    """
    Model for token usage.
    """
    prompt_tokens: int
    completion_tokens: Optional[int] = 0
    total_tokens: int


class ChatResponseChoice(BaseModel):
    """
    Model for a chat response choice.
    """
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class CompletionResponseChoice(BaseModel):
    """
    Model for a completion response choice.
    """
    index: int
    text: str
    finish_reason: Optional[str] = None


class EmbeddingResponseData(BaseModel):
    """
    Model for embedding response data.
    """
    index: int
    embedding: List[float]


class ImageResponseData(BaseModel):
    """
    Model for image response data.
    """
    url: str
    revised_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Model for a chat response.
    """
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatResponseChoice]
    usage: TokenUsage


class CompletionResponse(BaseModel):
    """
    Model for a completion response.
    """
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionResponseChoice]
    usage: TokenUsage


class EmbeddingResponse(BaseModel):
    """
    Model for an embedding response.
    """
    object: str = "embedding"
    model: str
    data: List[EmbeddingResponseData]
    usage: TokenUsage


class ImageGenerationResponse(BaseModel):
    """
    Model for an image generation response.
    """
    created: int
    data: List[ImageResponseData]


class AudioTranscriptionResponse(BaseModel):
    """
    Model for an audio transcription response.
    """
    text: str


class AudioTranslationResponse(BaseModel):
    """
    Model for an audio translation response.
    """
    text: str


class ModelResponseWrapper(BaseModel):
    """
    Union model for all response types.
    """
    response: Union[
        ChatResponse,
        CompletionResponse,
        EmbeddingResponse,
        ImageGenerationResponse,
        AudioTranscriptionResponse,
        AudioTranslationResponse,
    ]
    request_id: str
    model_id: str
    provider: str
    latency_ms: float
    cost: Optional[float] = None
