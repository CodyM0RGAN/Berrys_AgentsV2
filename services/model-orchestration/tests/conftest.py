import asyncio
import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Set up SQLAlchemy mocks before any imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Create a base declarative model
Base = declarative_base()

# Mock all shared modules before any imports
sys.modules['shared'] = MagicMock()
sys.modules['shared.utils'] = MagicMock()
sys.modules['shared.utils.src.database'] = MagicMock()
sys.modules['shared.utils.src.messaging'] = MagicMock()
sys.modules['shared.utils.logging'] = MagicMock()
sys.modules['shared.utils.auth'] = MagicMock()
sys.modules['shared.models'] = MagicMock()

# Set up database mocks
db_mock = AsyncMock()
db_mock.Base = Base
db_mock.get_db = AsyncMock()
db_mock.init_db = AsyncMock()
db_mock.close_db_connection = AsyncMock()
db_mock.check_db_connection = AsyncMock(return_value=True)
sys.modules['shared.utils.src.database'] = db_mock

# Set up messaging mocks
messaging_mock = AsyncMock()
messaging_mock.init_messaging = AsyncMock()
messaging_mock.close_messaging = AsyncMock()
messaging_mock.get_event_bus = AsyncMock()
messaging_mock.get_command_bus = AsyncMock()
sys.modules['shared.utils.src.messaging'] = messaging_mock

# Set up logging mocks
logging_mock = AsyncMock()
logging_mock.setup_logging = MagicMock()
logging_mock.get_logger = MagicMock()
sys.modules['shared.utils.logging'] = logging_mock

# Set up auth mocks
auth_mock = AsyncMock()
auth_mock.create_access_token = AsyncMock()
auth_mock.get_current_user = AsyncMock()
auth_mock.get_password_hash = MagicMock()
auth_mock.verify_password = MagicMock()
auth_mock.require_permission = MagicMock()
sys.modules['shared.utils.auth'] = auth_mock

# Create mock dependencies
async def get_db():
    """Mock database dependency."""
    yield None

async def get_event_bus():
    """Mock event bus dependency."""
    return AsyncMock()

async def get_command_bus():
    """Mock command bus dependency."""
    return AsyncMock()

# Now import FastAPI TestClient
from fastapi.testclient import TestClient

# Now import from src.main after all mocks are set up
from src.main import app
from src.config import get_settings, Settings
from src.providers.provider_factory import get_provider_factory
from src.providers.provider_interface import ModelProvider
from src.models.api import (
    ModelProvider as ModelProviderEnum,
    ModelCapability,
    ModelStatus,
)


# Test settings
@pytest.fixture
def test_settings():
    """
    Test settings fixture.
    """
    return Settings(
        environment="test",
        debug=True,
        service_name="model-orchestration-test",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        jwt_secret="test_secret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        openai_api_key="test_openai_api_key",
        anthropic_api_key="test_anthropic_api_key",
        ollama_url="http://localhost:11434",
        default_model="gpt-3.5-turbo",
        default_provider="openai",
        default_timeout=10.0,
        max_retries=1,
        retry_delay=0.1,
        max_input_tokens=8000,
        max_output_tokens=2000,
        token_buffer_percentage=0.1,
        enable_cost_tracking=True,
        enable_fallback=True,
        enable_caching=False,
        enable_streaming=True,
        enable_metrics=True,
    )


# Override settings for tests
@pytest.fixture(autouse=True)
def override_settings(test_settings):
    """
    Override settings for tests.
    """
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield
    app.dependency_overrides.clear()


# Database setup
@pytest_asyncio.fixture
async def async_db_engine():
    """
    Create async database engine.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_db_session(async_db_engine):
    """
    Create async database session.
    """
    async_session = sessionmaker(
        async_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session


# Override database dependency
@pytest.fixture
def override_db(async_db_session):
    """
    Override database dependency.
    """
    async def get_test_db():
        try:
            yield async_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


# Mock event bus
@pytest.fixture
def mock_event_bus():
    """
    Mock event bus.
    """
    mock = AsyncMock()
    mock.publish_event = AsyncMock()
    
    app.dependency_overrides[get_event_bus] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_event_bus, None)


# Mock command bus
@pytest.fixture
def mock_command_bus():
    """
    Mock command bus.
    """
    mock = AsyncMock()
    mock.send_command = AsyncMock()
    mock.register_handler = MagicMock()
    
    app.dependency_overrides[get_command_bus] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_command_bus, None)


# Mock database session
@pytest.fixture
def mock_db_session():
    """
    Mock database session.
    """
    mock = AsyncMock()
    mock.add = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.execute = AsyncMock()
    return mock


# Mock provider
class MockProvider(ModelProvider):
    """
    Mock provider for testing.
    """
    def __init__(self, settings):
        self.settings = settings
        self._available_models = {
            "gpt-3.5-turbo": {
                "id": "gpt-3.5-turbo",
                "provider": "openai",
                "capabilities": ["chat", "completion"],
                "token_limit": 4096,
                "pricing": {
                    "prompt": 0.0015,
                    "completion": 0.002,
                },
            },
            "text-embedding-ada-002": {
                "id": "text-embedding-ada-002",
                "provider": "openai",
                "capabilities": ["embedding"],
                "token_limit": 8191,
                "pricing": {
                    "prompt": 0.0001,
                    "completion": 0.0,
                },
            },
        }
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    @property
    def available_models(self) -> dict:
        return self._available_models
    
    async def initialize(self) -> None:
        pass
    
    async def validate_api_key(self) -> bool:
        return True
    
    async def chat_completion(self, request):
        from src.models.api import (
            ChatResponse,
            ChatResponseChoice,
            ChatMessage,
            MessageRole,
            TokenUsage,
        )
        return ChatResponse(
            id="mock-response-id",
            object="chat.completion",
            created=1234567890,
            model=request.model_id,
            choices=[
                ChatResponseChoice(
                    index=0,
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content="This is a mock response",
                    ),
                    finish_reason="stop",
                )
            ],
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
        )
    
    async def text_completion(self, request):
        from src.models.api import (
            CompletionResponse,
            CompletionResponseChoice,
            TokenUsage,
        )
        return CompletionResponse(
            id="mock-response-id",
            object="text_completion",
            created=1234567890,
            model=request.model_id,
            choices=[
                CompletionResponseChoice(
                    index=0,
                    text="This is a mock response",
                    finish_reason="stop",
                )
            ],
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
        )
    
    async def embedding(self, request):
        from src.models.api import (
            EmbeddingResponse,
            EmbeddingResponseData,
            TokenUsage,
        )
        return EmbeddingResponse(
            object="embedding",
            model=request.model_id,
            data=[
                EmbeddingResponseData(
                    index=0,
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                )
            ],
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=0,
                total_tokens=10,
            ),
        )
    
    async def image_generation(self, request):
        from src.models.api import (
            ImageGenerationResponse,
            ImageResponseData,
        )
        return ImageGenerationResponse(
            created=1234567890,
            data=[
                ImageResponseData(
                    url="https://example.com/image.png",
                    revised_prompt="A revised prompt",
                )
            ],
        )
    
    async def audio_transcription(self, request):
        from src.models.api import AudioTranscriptionResponse
        return AudioTranscriptionResponse(
            text="This is a mock transcription",
        )
    
    async def audio_translation(self, request):
        from src.models.api import AudioTranslationResponse
        return AudioTranslationResponse(
            text="This is a mock translation",
        )
    
    async def count_tokens(self, text, model_id):
        if isinstance(text, str):
            return len(text.split())
        elif isinstance(text, list):
            return sum(len(m.get("content", "").split()) for m in text)
        return 0
    
    def get_model_info(self, model_id):
        return self._available_models.get(model_id)
    
    def supports_model(self, model_id):
        return model_id in self._available_models or model_id.startswith("gpt-")
    
    def calculate_cost(self, model_id, prompt_tokens, completion_tokens):
        model_info = self.get_model_info(model_id)
        if not model_info or "pricing" not in model_info:
            return 0.0
        
        pricing = model_info["pricing"]
        prompt_cost = pricing.get("prompt", 0.0) * prompt_tokens / 1000
        completion_cost = pricing.get("completion", 0.0) * completion_tokens / 1000
        
        return prompt_cost + completion_cost


# Mock provider factory
@pytest.fixture
def mock_provider_factory(test_settings):
    """
    Mock provider factory.
    """
    from src.providers.provider_factory import ProviderFactory
    
    factory = ProviderFactory(test_settings)
    mock_provider = MockProvider(test_settings)
    factory.register_provider_class("mock", MockProvider)
    factory.providers = {"mock": mock_provider}
    
    with patch("src.providers.provider_factory.get_provider_factory", return_value=factory):
        yield factory


# Test client
@pytest.fixture
def client(override_db, mock_event_bus, mock_command_bus, mock_provider_factory):
    """
    Test client.
    """
    with TestClient(app) as client:
        yield client


# Test data
@pytest.fixture
def test_model_data():
    """
    Test model data.
    """
    return {
        "model_id": "gpt-3.5-turbo",
        "provider": ModelProviderEnum.OPENAI,
        "capabilities": [ModelCapability.CHAT],
        "status": ModelStatus.ACTIVE,
        "display_name": "GPT-3.5 Turbo",
        "description": "OpenAI's GPT-3.5 Turbo model",
        "max_tokens": 4096,
        "token_limit": 4096,
        "cost_per_token": 0.000002,
        "configuration": {
            "temperature": 0.7,
            "top_p": 1.0,
        },
        "metadata": {
            "version": "0613",
        },
    }


@pytest.fixture
def test_chat_request_data():
    """
    Test chat request data.
    """
    return {
        "model_id": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7,
    }


@pytest.fixture
def test_embedding_request_data():
    """
    Test embedding request data.
    """
    return {
        "model_id": "text-embedding-ada-002",
        "input": "This is a test sentence for embedding.",
    }
