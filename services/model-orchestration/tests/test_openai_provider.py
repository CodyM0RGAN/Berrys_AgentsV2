import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import openai

from src.config import Settings
from src.providers.openai_provider import OpenAIProvider
from src.models.api import (
    ChatRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    ChatMessage,
    MessageRole,
)
from src.exceptions import (
    ProviderAuthenticationError,
    ProviderNotAvailableError,
    RateLimitError,
    RequestTimeoutError,
    ContentFilterError,
    InvalidRequestError,
)


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client.
    """
    # Create mock client
    mock_client = MagicMock()
    
    # Mock models list
    mock_models_list = AsyncMock()
    mock_models_list.return_value.data = [
        MagicMock(id="gpt-3.5-turbo"),
        MagicMock(id="gpt-4"),
        MagicMock(id="text-embedding-ada-002"),
        MagicMock(id="dall-e-3"),
        MagicMock(id="whisper-1"),
    ]
    mock_client.models.list = mock_models_list
    
    # Mock chat completions
    mock_chat_completion = AsyncMock()
    mock_chat_completion.return_value = MagicMock(
        id="mock-chat-id",
        model="gpt-3.5-turbo",
        choices=[
            MagicMock(
                message=MagicMock(
                    role="assistant",
                    content="This is a mock chat response",
                ),
                finish_reason="stop",
            )
        ],
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )
    mock_client.chat.completions.create = mock_chat_completion
    
    # Mock completions
    mock_completion = AsyncMock()
    mock_completion.return_value = MagicMock(
        id="mock-completion-id",
        model="text-davinci-003",
        choices=[
            MagicMock(
                text="This is a mock completion response",
                finish_reason="stop",
            )
        ],
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )
    mock_client.completions.create = mock_completion
    
    # Mock embeddings
    mock_embedding = AsyncMock()
    mock_embedding.return_value = MagicMock(
        model="text-embedding-ada-002",
        data=[
            MagicMock(
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            )
        ],
        usage=MagicMock(
            prompt_tokens=10,
            total_tokens=10,
        ),
    )
    mock_client.embeddings.create = mock_embedding
    
    # Mock image generation
    mock_image_generation = AsyncMock()
    mock_image_generation.return_value = MagicMock(
        data=[
            MagicMock(
                url="https://example.com/image.png",
                revised_prompt="A revised prompt",
            )
        ],
    )
    mock_client.images.generate = mock_image_generation
    
    # Mock audio transcription
    mock_audio_transcription = AsyncMock()
    mock_audio_transcription.return_value = MagicMock(
        text="This is a mock transcription",
    )
    mock_client.audio.transcriptions.create = mock_audio_transcription
    
    # Mock audio translation
    mock_audio_translation = AsyncMock()
    mock_audio_translation.return_value = MagicMock(
        text="This is a mock translation",
    )
    mock_client.audio.translations.create = mock_audio_translation
    
    return mock_client


@pytest.fixture
def openai_provider(test_settings, mock_openai_client):
    """
    OpenAI provider fixture.
    """
    with patch("openai.AsyncOpenAI", return_value=mock_openai_client):
        provider = OpenAIProvider(test_settings)
        asyncio.run(provider.initialize())
        yield provider


class TestOpenAIProvider:
    """
    Tests for the OpenAI provider.
    """
    
    def test_provider_name(self, openai_provider):
        """
        Test provider name.
        """
        assert openai_provider.provider_name == "openai"
    
    def test_available_models(self, openai_provider):
        """
        Test available models.
        """
        models = openai_provider.available_models
        assert len(models) > 0
        assert "gpt-3.5-turbo" in models
        assert "gpt-4" in models
        assert "text-embedding-ada-002" in models
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, openai_provider, mock_openai_client):
        """
        Test successful API key validation.
        """
        # Set up mock
        mock_openai_client.models.list = AsyncMock()
        
        # Test
        result = await openai_provider.validate_api_key()
        
        # Verify
        assert result is True
        mock_openai_client.models.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, openai_provider, mock_openai_client):
        """
        Test failed API key validation.
        """
        # Set up mock
        # Create a proper APIError object with required parameters
        from httpx import Response
        mock_response = Response(status_code=401, content=b'{"error": {"message": "Invalid API key"}}')
        mock_openai_client.models.list = AsyncMock(
            side_effect=openai.AuthenticationError("Invalid API key", response=mock_response, body={"error": {"message": "Invalid API key"}})
        )
        
        # Test
        result = await openai_provider.validate_api_key()
        
        # Verify
        assert result is False
        mock_openai_client.models.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, openai_provider, mock_openai_client):
        """
        Test chat completion.
        """
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content="You are a helpful assistant.",
                ),
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello, how are you?",
                ),
            ],
            max_tokens=100,
            temperature=0.7,
        )
        
        # Test
        response = await openai_provider.chat_completion(request)
        
        # Verify
        assert response is not None
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) > 0
        assert response.choices[0].message.content == "This is a mock chat response"
        assert response.choices[0].message.role == MessageRole.ASSISTANT
        assert response.usage.prompt_tokens == 10
        assert response.usage.completion_tokens == 5
        assert response.usage.total_tokens == 15
        
        # Verify API call
        mock_openai_client.chat.completions.create.assert_called_once()
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-3.5-turbo"
        assert len(call_args["messages"]) == 2
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][0]["content"] == "You are a helpful assistant."
        assert call_args["messages"][1]["role"] == "user"
        assert call_args["messages"][1]["content"] == "Hello, how are you?"
        assert call_args["max_tokens"] == 100
        assert call_args["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_embedding(self, openai_provider, mock_openai_client):
        """
        Test embedding.
        """
        # Create request
        request = EmbeddingRequest(
            model_id="text-embedding-ada-002",
            input="This is a test sentence for embedding.",
        )
        
        # Test
        response = await openai_provider.embedding(request)
        
        # Verify
        assert response is not None
        assert response.model == "text-embedding-ada-002"
        assert len(response.data) > 0
        assert len(response.data[0].embedding) > 0
        assert response.usage.prompt_tokens == 10
        assert response.usage.total_tokens == 10
        
        # Verify API call
        mock_openai_client.embeddings.create.assert_called_once()
        call_args = mock_openai_client.embeddings.create.call_args[1]
        assert call_args["model"] == "text-embedding-ada-002"
        assert call_args["input"] == "This is a test sentence for embedding."
    
    @pytest.mark.asyncio
    async def test_count_tokens_string(self, openai_provider):
        """
        Test token counting for strings.
        """
        # Test
        token_count = await openai_provider.count_tokens("This is a test sentence.", "gpt-3.5-turbo")
        
        # Verify
        assert token_count > 0
    
    @pytest.mark.asyncio
    async def test_count_tokens_messages(self, openai_provider):
        """
        Test token counting for messages.
        """
        # Create messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ]
        
        # Test
        token_count = await openai_provider.count_tokens(messages, "gpt-3.5-turbo")
        
        # Verify
        assert token_count > 0
    
    def test_supports_model(self, openai_provider):
        """
        Test model support check.
        """
        # Test known models
        assert openai_provider.supports_model("gpt-3.5-turbo") is True
        assert openai_provider.supports_model("gpt-4") is True
        assert openai_provider.supports_model("text-embedding-ada-002") is True
        
        # Test unknown models with known prefixes
        assert openai_provider.supports_model("gpt-5") is True
        assert openai_provider.supports_model("text-new-model") is True
        
        # Test completely unknown models
        assert openai_provider.supports_model("unknown-model") is False
    
    def test_calculate_cost(self, openai_provider):
        """
        Test cost calculation.
        """
        # Test GPT-3.5 Turbo
        cost = openai_provider.calculate_cost("gpt-3.5-turbo", 1000, 500)
        expected_cost = (1000 * 0.0015 / 1000) + (500 * 0.002 / 1000)
        assert cost == pytest.approx(expected_cost)
        
        # Test GPT-4
        cost = openai_provider.calculate_cost("gpt-4", 1000, 500)
        expected_cost = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
        assert cost == pytest.approx(expected_cost)
        
        # Test embedding
        cost = openai_provider.calculate_cost("text-embedding-ada-002", 1000, 0)
        expected_cost = 1000 * 0.0001 / 1000
        assert cost == pytest.approx(expected_cost)


class TestOpenAIProviderErrors:
    """
    Tests for OpenAI provider error handling.
    """
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, openai_provider, mock_openai_client):
        """
        Test authentication error.
        """
        # Set up mock
        # Create a proper APIError object with required parameters
        from httpx import Response
        mock_response = Response(status_code=401, content=b'{"error": {"message": "Invalid API key"}}')
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.AuthenticationError("Invalid API key", response=mock_response, body={"error": {"message": "Invalid API key"}})
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(ProviderAuthenticationError):
            await openai_provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, openai_provider, mock_openai_client):
        """
        Test rate limit error.
        """
        # Set up mock
        # Create a proper APIError object with required parameters
        from httpx import Response
        mock_response = Response(status_code=429, content=b'{"error": {"message": "Rate limit exceeded"}}')
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError("Rate limit exceeded", response=mock_response, body={"error": {"message": "Rate limit exceeded"}})
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(RateLimitError):
            await openai_provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, openai_provider, mock_openai_client):
        """
        Test timeout error.
        """
        # Set up mock
        # Create a proper timeout error
        import httpx
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(
                "Request timed out",
                request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions')
            )
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(RequestTimeoutError):
            await openai_provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_content_filter_error(self, openai_provider, mock_openai_client):
        """
        Test content filter error.
        """
        # Set up mock
        # Create a proper BadRequestError with required parameters
        from httpx import Response
        mock_response = Response(
            status_code=400, 
            content=b'{"error": {"message": "Your request was rejected as a result of our safety system"}}'
        )
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.BadRequestError(
                "Your request was rejected as a result of our safety system",
                response=mock_response,
                body={"error": {"message": "Your request was rejected as a result of our safety system"}}
            )
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(ContentFilterError):
            await openai_provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_invalid_request_error(self, openai_provider, mock_openai_client):
        """
        Test invalid request error.
        """
        # Set up mock
        # Create a proper BadRequestError with required parameters
        from httpx import Response
        mock_response = Response(
            status_code=400, 
            content=b'{"error": {"message": "Invalid request"}}'
        )
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.BadRequestError(
                "Invalid request",
                response=mock_response,
                body={"error": {"message": "Invalid request"}}
            )
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(InvalidRequestError):
            await openai_provider.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_api_error(self, openai_provider, mock_openai_client):
        """
        Test API error.
        """
        # Set up mock
        # Create a proper APIError with required parameters
        import httpx
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIError(
                "API error", 
                request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions')
            )
        )
        
        # Create request
        request = ChatRequest(
            model_id="gpt-3.5-turbo",
            messages=[
                ChatMessage(
                    role=MessageRole.USER,
                    content="Hello",
                ),
            ],
        )
        
        # Test
        with pytest.raises(ProviderNotAvailableError):
            await openai_provider.chat_completion(request)
