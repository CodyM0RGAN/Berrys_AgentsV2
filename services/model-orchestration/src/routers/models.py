from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dependencies import get_model_service, get_current_user, get_optional_user, get_admin_user, UserInfo
from ..exceptions import ModelNotFoundError, InvalidRequestError
from ..models.api import (
    Model,
    ModelCreate,
    ModelUpdate,
    ModelList,
    ChatRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    AudioTranscriptionRequest,
    AudioTranslationRequest,
)
from ..models.api.responses import ModelResponseWrapper as ModelResponse
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus
from ..services.model_service import ModelService

router = APIRouter()


@router.post(
    "",
    response_model=Model,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new model",
    description="Register a new model with the provided data.",
)
async def register_model(
    model: ModelCreate,
    current_user: UserInfo = Depends(get_admin_user),
    model_service: ModelService = Depends(get_model_service),
) -> Model:
    """
    Register a new model.
    
    Args:
        model: Model data
        current_user: Current authenticated admin user
        model_service: Model service
        
    Returns:
        Model: Registered model
        
    Raises:
        InvalidRequestError: If model data is invalid
    """
    return await model_service.register_model(model)


@router.get(
    "",
    response_model=ModelList,
    summary="List models",
    description="Get a paginated list of models with optional filtering.",
)
async def list_models(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    provider: Optional[ModelProvider] = Query(None, description="Filter by provider"),
    capability: Optional[ModelCapability] = Query(None, description="Filter by capability"),
    status: Optional[ModelStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelList:
    """
    List models with pagination and filtering.
    
    Args:
        page: Page number
        page_size: Page size
        provider: Filter by provider
        capability: Filter by capability
        status: Filter by status
        search: Search term
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelList: Paginated list of models
    """
    # Get models
    models, total = await model_service.list_models(
        page=page,
        page_size=page_size,
        provider=provider.value if provider else None,
        capability=capability.value if capability else None,
        status=status.value if status else None,
        search=search,
    )
    
    # Return paginated list
    return ModelList(
        items=models,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{model_id}",
    response_model=Model,
    summary="Get model",
    description="Get a model by ID.",
)
async def get_model(
    model_id: str = Path(..., description="Model ID"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> Model:
    """
    Get a model by ID.
    
    Args:
        model_id: Model ID
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        Model: Model
        
    Raises:
        ModelNotFoundError: If model not found
    """
    # Get model
    model = await model_service.get_model(model_id)
    
    # Check if model exists
    if not model:
        raise ModelNotFoundError(model_id)
    
    return model


@router.put(
    "/{model_id}",
    response_model=Model,
    summary="Update model",
    description="Update a model by ID.",
)
async def update_model(
    model_update: ModelUpdate,
    model_id: str = Path(..., description="Model ID"),
    current_user: UserInfo = Depends(get_admin_user),
    model_service: ModelService = Depends(get_model_service),
) -> Model:
    """
    Update a model by ID.
    
    Args:
        model_update: Model update data
        model_id: Model ID
        current_user: Current authenticated admin user
        model_service: Model service
        
    Returns:
        Model: Updated model
        
    Raises:
        ModelNotFoundError: If model not found
        InvalidRequestError: If model data is invalid
    """
    # Get model
    model = await model_service.get_model(model_id)
    
    # Check if model exists
    if not model:
        raise ModelNotFoundError(model_id)
    
    # Update model
    updated_model = await model_service.update_model(model_id, model_update)
    
    return updated_model


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete model",
    description="Delete a model by ID.",
)
async def delete_model(
    model_id: str = Path(..., description="Model ID"),
    current_user: UserInfo = Depends(get_admin_user),
    model_service: ModelService = Depends(get_model_service),
) -> None:
    """
    Delete a model by ID.
    
    Args:
        model_id: Model ID
        current_user: Current authenticated admin user
        model_service: Model service
        
    Raises:
        ModelNotFoundError: If model not found
    """
    # Get model
    model = await model_service.get_model(model_id)
    
    # Check if model exists
    if not model:
        raise ModelNotFoundError(model_id)
    
    # Delete model
    await model_service.delete_model(model_id)


@router.post(
    "/chat",
    response_model=ModelResponse,
    summary="Chat completion",
    description="Send a chat completion request to a model.",
)
async def chat_completion(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send a chat completion request to a model.
    
    Args:
        request: Chat request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_chat_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="chat",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response


@router.post(
    "/completion",
    response_model=ModelResponse,
    summary="Text completion",
    description="Send a text completion request to a model.",
)
async def text_completion(
    request: CompletionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send a text completion request to a model.
    
    Args:
        request: Completion request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_completion_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="completion",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response


@router.post(
    "/embedding",
    response_model=ModelResponse,
    summary="Embedding",
    description="Send an embedding request to a model.",
)
async def embedding(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send an embedding request to a model.
    
    Args:
        request: Embedding request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_embedding_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="embedding",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response


@router.post(
    "/image",
    response_model=ModelResponse,
    summary="Image generation",
    description="Send an image generation request to a model.",
)
async def image_generation(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send an image generation request to a model.
    
    Args:
        request: Image generation request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_image_generation_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="image_generation",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response


@router.post(
    "/audio/transcription",
    response_model=ModelResponse,
    summary="Audio transcription",
    description="Send an audio transcription request to a model.",
)
async def audio_transcription(
    request: AudioTranscriptionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send an audio transcription request to a model.
    
    Args:
        request: Audio transcription request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_audio_transcription_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="audio_transcription",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response


@router.post(
    "/audio/translation",
    response_model=ModelResponse,
    summary="Audio translation",
    description="Send an audio translation request to a model.",
)
async def audio_translation(
    request: AudioTranslationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    model_service: ModelService = Depends(get_model_service),
) -> ModelResponse:
    """
    Send an audio translation request to a model.
    
    Args:
        request: Audio translation request
        background_tasks: Background tasks
        current_user: Current authenticated user (optional)
        model_service: Model service
        
    Returns:
        ModelResponse: Model response
        
    Raises:
        InvalidRequestError: If request is invalid
    """
    # Set user ID if authenticated
    if current_user and not request.user_id:
        request.user_id = current_user.id
    
    # Process request
    response = await model_service.process_audio_translation_request(request)
    
    # Log request in background
    background_tasks.add_task(
        model_service.log_request,
        request_id=response.request_id,
        request_type="audio_translation",
        model_id=response.model_id,
        provider=response.provider,
        user_id=request.user_id,
        project_id=request.project_id,
        task_id=request.task_id,
        request_data=request.dict(),
        response_data=response.response.dict(),
        latency_ms=response.latency_ms,
        cost=response.cost,
    )
    
    return response
