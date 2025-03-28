# Import models for easier access
from shared.models.src.chat import ChatMessage
from shared.models.src.api.responses import ErrorResponse
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus, RequestType, MessageRole

from .api import (
    # Enums are now imported from shared.models.src.enums above
    ModelBase,
    ModelCreate,
    ModelUpdate,
    ModelInDB,
    Model,
    RequestBase,
    ChatRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    AudioTranscriptionRequest,
    AudioTranslationRequest,
    ModelRequest,
    TokenUsage,
    ChatResponseChoice,
    CompletionResponseChoice,
    EmbeddingResponseData,
    ImageResponseData,
    ChatResponse,
    CompletionResponse,
    EmbeddingResponse,
    ImageGenerationResponse,
    AudioTranscriptionResponse,
    AudioTranslationResponse,
    ModelResponseWrapper,
)

from .internal import (
    ModelModel,
    RequestModel,
    ProviderQuotaModel,
)

__all__ = [
    # API models
    "ModelProvider",
    "ModelCapability",
    "ModelStatus",
    "RequestType",
    "MessageRole",
    "ChatMessage",
    "ModelBase",
    "ModelCreate",
    "ModelUpdate",
    "ModelInDB",
    "Model",
    "RequestBase",
    "ChatRequest",
    "CompletionRequest",
    "EmbeddingRequest",
    "ImageGenerationRequest",
    "AudioTranscriptionRequest",
    "AudioTranslationRequest",
    "ModelRequest",
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
    "ErrorResponse",
    
    # Internal models
    "ModelModel",
    "RequestModel",
    "ProviderQuotaModel",
]
